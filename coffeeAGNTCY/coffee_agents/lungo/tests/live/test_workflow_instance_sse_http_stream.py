# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""HTTP-level check: GET instance SSE stream receives ``event_v1`` after POST.

Uses a short-lived ``uvicorn`` subprocess because in-process ASGI clients
(``TestClient``, ``httpx.ASGITransport``) await the full ASGI call until the
response body completes, which never happens for an infinite SSE stream.

The SSE body is read with a raw TCP ``socket``: ``httpx`` sync streaming can
stall on long-lived chunked responses even against a real server.

``POST .../events/`` requires the instance to exist (via ``POST .../`` first),
matching production UI and agent flows.
"""

from __future__ import annotations

import subprocess
import threading
import time
from urllib.parse import quote
from uuid import UUID

import httpx
import pytest
from schema.types import Event

from tests.helpers.workflow_api_auth import workflow_api_auth_headers
from tests.helpers.agentic_uvicorn_helpers import (
    assert_lungo_package_layout,
    first_sse_data_payload,
    free_tcp_port,
    minimal_event_v1_dict,
    read_sse_until_data_line,
    start_agentic_uvicorn,
    wait_health,
)


def test_sse_stream_receives_event_after_post() -> None:
    assert_lungo_package_layout()
    port = free_tcp_port()
    base_url = f"http://127.0.0.1:{port}"
    proc = start_agentic_uvicorn(port)
    try:
        wait_health(base_url)
        api_headers = workflow_api_auth_headers()

        wf = "A2A HTTP"
        wf_seg = quote(wf, safe="")
        with httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(30.0),
            trust_env=False,
            headers=api_headers,
        ) as hc:
            ir = hc.post(f"/agentic-workflows/{wf_seg}/")
            assert ir.status_code == 200, ir.text
            wid = ir.json()["workflow_instance_id"]
            assert wid.startswith("instance://")
            path_uuid = UUID(wid.removeprefix("instance://"))

            dr = hc.get(f"/agentic-workflows/{wf_seg}/")
            assert dr.status_code == 200, dr.text
            detail = dr.json()

        event_id = "event://550e8400-e29b-41d4-a716-4466554400c1"
        post_path = f"/agentic-workflows/{wf_seg}/instances/{path_uuid}/events/"
        stream_path = (
            f"/agentic-workflows/{wf_seg}/instances/{path_uuid}/events/stream"
        )
        body = minimal_event_v1_dict(
            wf,
            wid,
            event_id,
            pattern=detail["pattern"],
            use_case=detail["use_case"],
            scenario=detail.get("scenario") or detail["use_case"],
            workflow_display_name=detail["name"],
        )

        post_status: dict[str, int | str] = {}

        def delayed_post() -> None:
            time.sleep(0.12)
            try:
                with httpx.Client(
                    base_url=base_url,
                    timeout=httpx.Timeout(10.0),
                    trust_env=False,
                    headers=api_headers,
                ) as pc:
                    pr = pc.post(post_path, json=body)
                    post_status["code"] = pr.status_code
                    if pr.status_code != 204:
                        post_status["body"] = pr.text[:500]
            except Exception as exc:  # noqa: BLE001
                post_status["err"] = repr(exc)

        poster = threading.Thread(target=delayed_post, daemon=True)
        poster.start()

        buf = read_sse_until_data_line("127.0.0.1", port, stream_path)

        poster.join(timeout=15.0)
        assert post_status.get("err") is None, post_status
        assert post_status.get("code") == 204, post_status
        assert b"data:" in buf, buf[:500]

        parsed = first_sse_data_payload(buf)
        assert parsed["metadata"]["id"] == event_id
        Event.model_validate(parsed)
        assert wid in parsed["data"]["workflows"][wf]["instances"]
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
