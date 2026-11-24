# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""ProcessRunner must notice a dead agent, and stop must take its children with it."""

import os
import sys
import time

import pytest

from tests.integration.helpers.process_helper import ProcessRunner

_SLEEP_CHILD = "import time; time.sleep(120)"


def test_wait_ready_reports_an_early_exit(tmp_path):
    runner = ProcessRunner(
        name="early-exit",
        cmd=[sys.executable, "-c", "import sys; sys.exit(3)"],
        ready_pattern="Agent ready",
        timeout_s=30,
        log_dir=tmp_path,
    ).start()
    started = time.monotonic()
    try:
        with pytest.raises(TimeoutError, match="exited with status 3"):
            runner.wait_ready()
    finally:
        runner.stop()
    assert time.monotonic() - started < 5


def test_stop_kills_children_in_the_process_group(tmp_path):
    script = (
        "import subprocess, sys, time\n"
        f"child = subprocess.Popen([sys.executable, '-c', {_SLEEP_CHILD!r}])\n"
        "print(f'child {child.pid}', flush=True)\n"
        "print('Agent ready', flush=True)\n"
        "time.sleep(120)\n"
    )
    runner = ProcessRunner(
        name="group-stop",
        cmd=[sys.executable, "-c", script],
        ready_pattern="Agent ready",
        timeout_s=10,
        log_dir=tmp_path,
    ).start()
    child_pid = None
    try:
        runner.wait_ready()
        for line in runner.tail().splitlines():
            if line.startswith("child "):
                child_pid = int(line.split()[1])
        assert child_pid is not None
    finally:
        runner.stop()

    assert runner._proc is not None
    assert runner._proc.poll() is not None
    with pytest.raises(ProcessLookupError):
        os.kill(child_pid, 0)
