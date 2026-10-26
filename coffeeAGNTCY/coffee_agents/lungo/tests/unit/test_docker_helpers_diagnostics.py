# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""The Docker test helper must not print the resolved compose config on failure.

``docker compose config`` expands every ``${VAR}`` from the process environment,
which in lungo includes LLM and API credentials, so printing it on a failed
command would leak them into test and CI logs.
"""

import importlib.util
import subprocess
from pathlib import Path

import pytest

HELPERS = (
    Path(__file__).resolve().parents[1]
    / "integration"
    / "helpers"
    / "docker_helpers.py"
)


@pytest.fixture
def docker_helpers():
    spec = importlib.util.spec_from_file_location("lungo_docker_helpers", HELPERS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_failed_command_prints_docker_stderr(docker_helpers, monkeypatch, capsys):
    def fake_run(cmd, *args, **kwargs):
        raise subprocess.CalledProcessError(
            1, cmd, stderr="Bind for 0.0.0.0:46357 failed: port is already allocated"
        )

    monkeypatch.setattr(docker_helpers.subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError):
        docker_helpers._run(["docker", "compose", "-f", "x.yaml", "up", "-d", "slim"])

    assert "port is already allocated" in capsys.readouterr().out


def test_failed_command_never_prints_resolved_config(docker_helpers, monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(list(cmd))
        if len(calls) == 1:
            raise subprocess.CalledProcessError(1, cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(docker_helpers.subprocess, "run", fake_run)

    with pytest.raises(subprocess.CalledProcessError):
        docker_helpers._run(["docker", "compose", "-f", "x.yaml", "up", "-d", "slim"])

    config_calls = [c for c in calls[1:] if "config" in c]
    assert config_calls, "the failure diagnostics should still list the services"
    for cmd in config_calls:
        assert cmd[-2:] == ["config", "--services"], cmd
