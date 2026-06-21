# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Live smoke test for POST /patterns/{name}/chat against a real LLM proxy.

Spins a short-lived uvicorn subprocess (TestClient buffers streaming responses
and breaks ADK's async LiteLLM client), then issues a real request against the
LiteLLM proxy configured in the environment.

Skipped unless LITELLM_PROXY_BASE_URL and LITELLM_PROXY_API_KEY are both set.
"""

from __future__ import annotations

import json
import os
import subprocess
from urllib.parse import quote

import httpx
import pytest
from tests.helpers.workflow_api_auth import workflow_api_auth_headers
from tests.unit.agentic_workflows.api.agentic_uvicorn_helpers import (
    assert_lungo_package_layout,
    free_tcp_port,
    start_agentic_uvicorn,
    wait_health,
)


pytestmark = pytest.mark.skipif(
    not (os.getenv("LITELLM_PROXY_BASE_URL") and os.getenv("LITELLM_PROXY_API_KEY")),
    reason="LITELLM_PROXY_BASE_URL / LITELLM_PROXY_API_KEY not configured",
)


def test_live_pattern_chat_streams_real_response() -> None:
    assert_lungo_package_layout()
    port = free_tcp_port()
    base_url = f"http://127.0.0.1:{port}"
    proc = start_agentic_uvicorn(port)
    try:
        wait_health(base_url)

        path = f"/patterns/{quote('Feedback Loop', safe='')}/chat"
        body = {
            "session_id": "live-smoke-1",
            "message": "In one sentence, what is the Feedback Loop pattern?",
        }
        with httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(60.0),
            trust_env=False,
            headers=workflow_api_auth_headers(),
        ) as client:
            with client.stream("POST", path, json=body) as r:
                assert r.status_code == 200
                assert r.headers["content-type"].startswith("application/x-ndjson")
                lines = [json.loads(line) for line in r.iter_lines() if line]

        response_chunks = [line["response"] for line in lines if "response" in line]
        errors = [line for line in lines if "error" in line]
        assert not errors, f"unexpected error line(s): {errors}"
        assert response_chunks, "expected at least one response chunk"
        assert lines[-1] == {"done": True}, f"stream should end with done; got {lines[-1]}"
        full = "".join(response_chunks).strip()
        assert len(full) > 20, f"response unexpectedly short: {full!r}"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
