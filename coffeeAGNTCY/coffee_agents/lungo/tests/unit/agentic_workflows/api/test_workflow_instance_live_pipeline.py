# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""End-to-end pipeline on a real uvicorn ``api.agentic_workflows.server:app``.

Catalog → instantiate → list → GET state → SSE after threaded POST.
Skip quick runs with: ``pytest -m "not live_server"``.

Uses subprocess + ``httpx`` for finite routes and raw socket for SSE (see
``agentic_uvicorn_helpers``); do not use ``TestClient`` for the event stream.
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
from tests.unit.agentic_workflows.api.agentic_uvicorn_helpers import (
    assert_lungo_package_layout,
    first_sse_data_payload,
    free_tcp_port,
    minimal_event_v1_dict,
    read_sse_until_data_line,
    start_agentic_uvicorn,
    wait_health,
)


@pytest.mark.live_server
def test_agentic_workflows_catalog_instantiate_list_state_events_sse() -> None:
    assert_lungo_package_layout()
    port = free_tcp_port()
    base_url = f"http://127.0.0.1:{port}"
    proc = start_agentic_uvicorn(port)
    try:
        wait_health(base_url)
        api_headers = workflow_api_auth_headers()
        with httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(30.0),
            trust_env=False,
            headers=api_headers,
        ) as hc:
            lr = hc.get("/agentic-workflows/")
            assert lr.status_code == 200, lr.text
            catalog = lr.json()
            if not catalog:
                pytest.skip("No workflows in catalog (empty starting_workflows load)")
            # Lexicographic first key — stable across runs (dict iteration order is not a contract).
            wf_name = min(catalog, key=str)

            dr = hc.get(f"/agentic-workflows/{wf_name}/")
            assert dr.status_code == 200, dr.text
            detail = dr.json()
            pattern = detail["pattern"]
            use_case = detail["use_case"]
            scenario = detail.get("scenario") or use_case
            wf_display_name = detail["name"]

            ir = hc.post(f"/agentic-workflows/{wf_name}/")
            assert ir.status_code == 200, ir.text
            wid = ir.json()["workflow_instance_id"]
            assert wid.startswith("instance://")
            path_uuid = UUID(wid.removeprefix("instance://"))

            listed = hc.get(f"/agentic-workflows/{wf_name}/instances/")
            assert listed.status_code == 200
            instances_map = listed.json()
            assert wid in instances_map

            sr = hc.get(f"/agentic-workflows/{wf_name}/instances/{path_uuid}/")
            assert sr.status_code == 200
            state = sr.json()
            assert state["id"] == wid
            assert "topology" in state

        event_id = "event://550e8400-e29b-41d4-a716-4466554400e0"
        post_path = f"/agentic-workflows/{wf_name}/instances/{path_uuid}/events/"
        # Raw HTTP request line must not contain unencoded spaces (httpx encodes paths for us).
        wf_path_seg = quote(wf_name, safe="")
        stream_path = (
            f"/agentic-workflows/{wf_path_seg}/instances/{path_uuid}/events/stream"
        )
        body = minimal_event_v1_dict(
            wf_name,
            wid,
            event_id,
            pattern=pattern,
            use_case=use_case,
            scenario=scenario,
            workflow_display_name=wf_display_name,
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
        assert b"data:" in buf, buf[:500]

        poster.join(timeout=15.0)
        assert post_status.get("err") is None, post_status.get("err")
        assert post_status.get("code") == 204, post_status

        parsed = first_sse_data_payload(buf)
        assert parsed["metadata"]["id"] == event_id
        Event.model_validate(parsed)
        assert wid in parsed["data"]["workflows"][wf_name]["instances"]
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
