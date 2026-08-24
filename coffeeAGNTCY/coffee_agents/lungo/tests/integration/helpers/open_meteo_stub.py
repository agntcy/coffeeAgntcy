# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Controllable local stub for Open-Meteo HTTP API used in integration tests."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Literal

StubMode = Literal["success", "error"]

STUB_CURRENT_WEATHER = {
    "time": "2025-01-01T12:00",
    "temperature": 22.0,
    "windspeed": 1.5,
    "winddirection": 270,
}


def stub_forecast_json() -> dict:
    return {"current_weather": dict(STUB_CURRENT_WEATHER)}


class OpenMeteoStubServer:
    """Thread-safe HTTP stub with success and error modes."""

    def __init__(self) -> None:
        self._mode: StubMode = "success"
        self._lock = threading.Lock()
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.port: int = 0
        self.url: str = ""

    def set_mode(self, mode: StubMode) -> None:
        with self._lock:
            self._mode = mode

    def get_mode(self) -> StubMode:
        with self._lock:
            return self._mode

    def start(self) -> None:
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                return

            def do_GET(self):
                mode = stub.get_mode()
                if mode == "error":
                    self.send_response(503)
                    self.end_headers()
                    self.wfile.write(b"service unavailable")
                    return

                payload = json.dumps(stub_forecast_json()).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        host, port = self._server.server_address
        self.port = int(port)
        self.url = f"http://{host}:{self.port}"

        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def forecast_base_url(self) -> str:
        return f"{self.url}/v1/forecast"
