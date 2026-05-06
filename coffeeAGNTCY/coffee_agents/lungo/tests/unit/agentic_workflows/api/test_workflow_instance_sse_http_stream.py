# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""HTTP-level check: GET instance SSE stream receives ``event_v1`` after POST.

Uses a short-lived ``uvicorn`` subprocess because in-process ASGI clients
(``TestClient``, ``httpx.ASGITransport``) await the full ASGI call until the
response body completes, which never happens for an infinite SSE stream.

The SSE body is read with a raw TCP ``socket``: ``httpx`` sync streaming can
stall on long-lived chunked responses even against a real server.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from uuid import UUID

import httpx
from schema.types import Event, instance_id_from_uuid

_LUNGO_ROOT = Path(__file__).resolve().parents[4]


def _event_dict(workflow_name: str, instance_uri: str, event_id: str) -> dict:
    return {
        "metadata": {
            "timestamp": "2026-01-01T00:00:00Z",
            "schema_version": "1.0.0",
            "correlation": {"id": "correlation://550e8400-e29b-41d4-a716-446655440001"},
            "id": event_id,
            "type": "StateProgressUpdate",
            "source": "test",
        },
        "data": {
            "workflows": {
                workflow_name: {
                    "name": workflow_name,
                    "pattern": "p",
                    "use_case": "u",
                    "scenario": "s",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        instance_uri: {
                            "id": instance_uri,
                            "topology": {},
                        }
                    },
                }
            }
        },
    }


def _first_sse_data_payload(buf: bytes) -> dict:
    marker = b"data:"
    pos = buf.find(marker)
    assert pos != -1, f"expected SSE data line in buffer, got {buf!r}"
    line_start = pos
    nl = buf.find(b"\n", line_start)
    assert nl != -1
    line = buf[line_start:nl].decode()
    assert line.startswith("data:")
    json_part = line[len("data:") :].strip()
    return json.loads(json_part)


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_health(base_url: str, *, deadline_s: float = 15.0) -> None:
    deadline = time.monotonic() + deadline_s
    last_err: Exception | None = None
    with httpx.Client(
        base_url=base_url,
        timeout=httpx.Timeout(2.0),
        trust_env=False,
    ) as client:
        while time.monotonic() < deadline:
            try:
                r = client.get("/health")
                if r.status_code == 200:
                    return
            except (httpx.ConnectError, httpx.ReadTimeout) as exc:
                last_err = exc
            time.sleep(0.05)
    msg = f"server did not become ready at {base_url}"
    if last_err is not None:
        raise AssertionError(msg) from last_err
    raise AssertionError(msg)


def _assert_lungo_layout() -> None:
    assert (_LUNGO_ROOT / "api" / "agentic_workflows" / "server.py").is_file(), (
        f"unexpected _LUNGO_ROOT {_LUNGO_ROOT}; fix parents[N] in this test module"
    )


def _read_sse_until_data_line(
    host: str,
    port: int,
    path: str,
    *,
    overall_deadline_s: float = 30.0,
) -> bytes:
    """HTTP/1.1 GET ``path``; return bytes containing at least one ``data:`` SSE line."""
    buf = b""
    end = time.monotonic() + overall_deadline_s
    with socket.create_connection((host, port), timeout=10) as sock:
        sock.settimeout(1.0)
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Accept: text/event-stream\r\n"
            "Cache-Control: no-cache\r\n"
            "\r\n"
        ).encode()
        sock.sendall(req)
        while time.monotonic() < end:
            try:
                chunk = sock.recv(8192)
            except socket.timeout:
                continue
            if not chunk:
                break
            buf += chunk
            if b"data:" in buf:
                return buf
            if b"\r\n\r\n" in buf:
                head, _, _ = buf.partition(b"\r\n\r\n")
                assert b" 200 " in head or b" 200\r\n" in head, head[:200]
                assert b"text/event-stream" in head.lower(), head[:400]
    return buf


def test_sse_stream_receives_event_after_post() -> None:
    _assert_lungo_layout()
    port = _free_tcp_port()
    base_url = f"http://127.0.0.1:{port}"
    env = {**os.environ, "PYTHONPATH": str(_LUNGO_ROOT)}
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api.agentic_workflows.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(_LUNGO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_health(base_url)

        uid = UUID("550e8400-e29b-41d4-a716-4466554400c0")
        iuri = instance_id_from_uuid(uid).root
        wf = "stream_http_wf"
        event_id = "event://550e8400-e29b-41d4-a716-4466554400c1"
        post_path = f"/agentic-workflows/{wf}/instances/{uid}/events/"
        stream_path = f"/agentic-workflows/{wf}/instances/{uid}/events/stream"
        body = _event_dict(wf, iuri, event_id)

        post_status: dict[str, int | str] = {}

        def delayed_post() -> None:
            time.sleep(0.12)
            try:
                with httpx.Client(
                    base_url=base_url,
                    timeout=httpx.Timeout(10.0),
                    trust_env=False,
                ) as pc:
                    pr = pc.post(post_path, json=body)
                    post_status["code"] = pr.status_code
                    if pr.status_code != 204:
                        post_status["body"] = pr.text[:500]
            except Exception as exc:  # noqa: BLE001
                post_status["err"] = repr(exc)

        poster = threading.Thread(target=delayed_post, daemon=True)
        poster.start()

        buf = _read_sse_until_data_line("127.0.0.1", port, stream_path)
        assert b"data:" in buf, buf[:500]

        poster.join(timeout=15.0)
        assert post_status.get("err") is None, post_status.get("err")
        assert post_status.get("code") == 204, post_status

        parsed = _first_sse_data_payload(buf)
        assert parsed["metadata"]["id"] == event_id
        Event.model_validate(parsed)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
