# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared helpers for uvicorn subprocess + raw-socket SSE tests under ``api/``."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx

from tests.helpers.workflow_api_auth import (
    TEST_WORKFLOW_API_KEY,
    workflow_api_auth_headers,
)

LUNGO_ROOT = Path(__file__).resolve().parents[4]


def assert_lungo_package_layout() -> None:
    assert (LUNGO_ROOT / "api" / "agentic_workflows" / "server.py").is_file(), (
        f"unexpected LUNGO_ROOT {LUNGO_ROOT}; fix parents[N] in agentic_uvicorn_helpers"
    )


def free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def start_agentic_uvicorn(port: int) -> subprocess.Popen:
    """Run ``api.agentic_workflows.server:app`` on ``127.0.0.1:port`` (stdout/stderr discarded)."""
    env = {
        **os.environ,
        "PYTHONPATH": str(LUNGO_ROOT),
        "WORKFLOW_API_KEY": TEST_WORKFLOW_API_KEY,
    }
    return subprocess.Popen(
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
        cwd=str(LUNGO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wait_health(base_url: str, *, deadline_s: float = 15.0) -> None:
    deadline = time.monotonic() + deadline_s
    last_err: Exception | None = None
    with httpx.Client(
        base_url=base_url,
        timeout=httpx.Timeout(2.0),
        trust_env=False,
        headers=workflow_api_auth_headers(),
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


def minimal_event_v1_dict(
    workflow_name: str,
    instance_uri: str,
    event_id: str,
    *,
    pattern: str = "p",
    use_case: str = "u",
    scenario: str = "s",
    workflow_display_name: str | None = None,
) -> dict:
    """Wire-shape ``event_v1`` for POST .../events/ (defaults match legacy SSE HTTP test)."""
    name = workflow_display_name if workflow_display_name is not None else workflow_name
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
                    "name": name,
                    "pattern": pattern,
                    "use_case": use_case,
                    "scenario": scenario,
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


def first_sse_data_payload(buf: bytes) -> dict:
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


def read_sse_until_data_line(
    host: str,
    port: int,
    path: str,
    *,
    extra_headers: dict[str, str] | None = None,
    overall_deadline_s: float = 30.0,
) -> bytes:
    """HTTP/1.1 GET ``path``; return bytes containing at least one ``data:`` SSE line."""
    buf = b""
    end = time.monotonic() + overall_deadline_s
    hdrs = extra_headers if extra_headers is not None else workflow_api_auth_headers()
    header_block = "".join(f"{k}: {v}\r\n" for k, v in hdrs.items())
    with socket.create_connection((host, port), timeout=10) as sock:
        sock.settimeout(1.0)
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Accept: text/event-stream\r\n"
            "Cache-Control: no-cache\r\n"
            f"{header_block}"
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
