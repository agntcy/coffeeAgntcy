# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# Lightweight threaded subprocess runner with prefixed logs + readiness gate.
# No external deps; perfect for pytest fixtures.

from __future__ import annotations
import os
import signal
import subprocess
import threading
import sys
import re
import time
from pathlib import Path
from datetime import datetime
from itertools import islice


class ProcessRunner:
    """
    Start a subprocess, stream logs (stdout+stderr) to console with a prefix
    and into a file, wait for a readiness pattern, and stop cleanly.
    """

    def __init__(
        self,
        name: str,
        cmd: list[str],
        cwd: str | None = None,
        env: dict | None = None,
        ready_pattern: str | None = None,
        timeout_s: float = 30.0,
        log_dir: Path | str = ".pytest-logs",
    ):
        self.name = name
        self.cmd = cmd
        self.cwd = cwd
        self.env = env
        self.timeout_s = timeout_s
        self.ready_re = re.compile(ready_pattern) if ready_pattern else None

        self._proc: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._ready = threading.Event()

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.log_dir / f"{name}.log"

    # --- public api ---------------------------------------------------------

    def start(self) -> "ProcessRunner":
        """Launch the process and begin streaming logs."""
        self._rotate_log_if_exists()
        self._proc = subprocess.Popen(
            self.cmd,
            cwd=self.cwd,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            text=True,
            start_new_session=True,  # so we can kill the whole process group
        )

        self._thread = threading.Thread(
            target=self._pump, name=f"{self.name}-logger", daemon=True
        )
        self._thread.start()
        return self

    def wait_ready(self):
        """Block until the ready pattern appears, the process exits, or timeout."""
        if not self.ready_re:
            return
        deadline = time.monotonic() + self.timeout_s
        while not self._ready.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._fail_not_ready(
                    f"{self.name} did not become ready within {self.timeout_s}s "
                    f"(pattern: {self.ready_re.pattern!r})"
                )
            if self._ready.wait(timeout=min(0.2, remaining)):
                return
            returncode = self._proc.poll() if self._proc is not None else None
            if returncode is not None:
                # The exit can land in the pipe before the pump thread marks ready.
                if self._thread is not None:
                    self._thread.join(timeout=1)
                if self._ready.is_set():
                    return
                self._fail_not_ready(
                    f"{self.name} exited with status {returncode} "
                    f"before becoming ready (pattern: {self.ready_re.pattern!r})"
                )

    def stop(self):
        """Stop the process and every child it spawned, then wait until they exit."""
        self._stop.set()
        proc = self._proc
        if proc is not None and proc.poll() is None:
            self._signal_group(signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._signal_group(signal.SIGKILL)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        # Avoid ResourceWarning: unclosed file from PIPE after the pump thread stops.
        if self._proc and self._proc.stdout is not None:
            try:
                self._proc.stdout.close()
            except OSError:
                pass

    def tail(self, n: int = 200) -> str:
        """Return the last N lines of the log file."""
        try:
            with open(self.log_path, "r", errors="replace") as f:
                total = sum(1 for _ in f)
                f.seek(0)
                return "".join(list(islice(f, max(0, total - n), None)))
        except Exception as e:
            return f"<could not read {self.log_path}: {e}>"

    # --- internals ----------------------------------------------------------

    def _fail_not_ready(self, message: str) -> None:
        sys.stdout.write(f"\n==== {self.name} (last 200 lines) ====\n")
        sys.stdout.write(self.tail(200) + "\n")
        raise TimeoutError(message)

    def _signal_group(self, sig: int) -> None:
        """Signal the child's session. ``start_new_session`` makes its pid the group id."""
        proc = self._proc
        if proc is None:
            return
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        except OSError:
            try:
                proc.send_signal(sig)
            except OSError:
                pass

    def _pump(self):
        assert self._proc is not None
        assert self._proc.stdout is not None

        prefix = f"[{self.name}] "
        with open(self.log_path, "w", buffering=1, errors="replace") as lf:
            for line in self._proc.stdout:
                if line is None:
                    break
                sys.stdout.write(prefix + line)
                lf.write(line)
                if self.ready_re and not self._ready.is_set():
                    if self.ready_re.search(line):
                        self._ready.set()
                if self._stop.is_set():
                    break

    def _rotate_log_if_exists(self):
        if self.log_path.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_path.rename(self.log_dir / f"{self.name}.{ts}.log")
