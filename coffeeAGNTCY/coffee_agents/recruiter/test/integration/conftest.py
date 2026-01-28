# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys
import os
import signal
import time
import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def run_recruiter_a2a_server():
    """Fixture to run the recruiter A2A server in a subprocess."""

    procs = []

    def _run(
    ):
        # Use the same Python interpreter as the test
        process = subprocess.Popen(
            [sys.executable, "src/agent_recruiter/server/server.py"],
            env={**os.environ, "ENABLE_HTTP": "true"},
            #tdout=subprocess.PIPE,
            #stderr=subprocess.PIPE,
            start_new_session=True,  # Create new process group for clean shutdown
        )
        procs.append(process)

        time.sleep(2)  # Wait for server to start
        return process

    yield _run

    # Cleanup: terminate all server processes
    for proc in procs:
        if proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                # Force kill if graceful shutdown fails
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass