# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
"""
Pytest fixtures using the simple ProcessRunner.
Replace prior xprocess usage with these.
"""
import os
from pathlib import Path
import pytest
import re
import sys
import time

from fastapi.testclient import TestClient

from tests.integration.docker_helpers import up, down
from tests.integration.process_helper import ProcessRunner 



AGENTS = {
    "farm": {
        "cmd": ["python", "-m", "farm.farm_server", "--no-reload"],
        "ready_pattern": r"Transport initialized with tracing enabled",
    }
}

_ACTIVE_RUNNERS = []

CORTO_DIR = Path(__file__).resolve().parents[2]

# ---------------- utils ----------------

def _base_env():
    return {
        **os.environ,
        "PYTHONPATH": CORTO_DIR,
        "ENABLE_HTTP": "true",
    }

def _purge_modules(prefixes):
    to_delete = [m for m in list(sys.modules)
                 if any(m == p or m.startswith(p + ".") for p in prefixes)]
    for m in to_delete:
        sys.modules.pop(m, None)

# ---------------- session infra ----------------
files = ["docker-compose.yaml"]
if Path("docker-compose.override.yaml").exists():
    files.append("docker-compose.override.yaml")
 
@pytest.fixture(scope="session", autouse=True)
def orchestrate_session_services():
    print("\n--- Setting up session level service integrations ---")
    setup_transports()
    setup_observability()
    setup_identity()
    print("--- Session level service setup complete. Tests can now run ---")
    yield
    down(files)

def setup_transports():
    _startup_slim()
    _startup_nats()

def setup_observability():
    _startup_otel_collector()
    _startup_clickhouse()
    _startup_grafana()

def setup_identity():
    pass

def _startup_slim():
    up(files, ["slim"])

def _startup_nats():
    up(files, ["nats"])

def _startup_grafana():
    up(files, ["grafana"])

def _startup_clickhouse():
    up(files, ["clickhouse-server"])

def _startup_otel_collector():
    up(files, ["otel-collector"])
    time.sleep(10)

# ---------------- per-test config ----------------

@pytest.fixture(scope="function")
def transport_config(request):
    return dict(getattr(request, "param", {}) or {})

@pytest.fixture(scope="function")
def agent_specs(request):
    """
    Select agents via @pytest.mark.agents([...])

    Each entry can be:
      - dict: {"name": str, "cmd": list[str], "ready_pattern": str?}
      - string module path: "agents.supervisors.auction.main" (runs with python -m)
    """
    m = request.node.get_closest_marker("agents")
    if not m:
        return []
    specs = m.args[0] if m.args else m.kwargs.get("specs", [])
    return [_normalize_agent_spec(s) for s in specs]

def _normalize_agent_spec(spec):
    """
    Return a dict: {"name": str, "cmd": list[str], "ready_pattern": str}
    """
    if isinstance(spec, dict):
        name = spec.get("name")
        cmd = spec.get("cmd")
        if not name:
            # try to derive a name from cmd or module
            name = _derive_name_from_spec(spec)
        ready = "Started server process"
        return {"name": name, "cmd": cmd, "ready_pattern": ready}

    if isinstance(spec, str):
        # If it's a python module path like "a.b.c", run it via python -m
        if re.match(r"^[a-zA-Z_][\w\.]*$", spec):
            return {
                "name": spec.split(".")[-1],
                "cmd": ["python", "-m", spec],
                "ready_pattern": "Transport initialized with tracing enabled",
            }
        raise ValueError(f"Unrecognized agent spec string: {spec!r}")

    raise TypeError(f"Agent spec must be dict or module string, got: {type(spec)}")

def _derive_name_from_spec(spec: dict) -> str:
    if "name" in spec and spec["name"]:
        return spec["name"]
    if "cmd" in spec and spec["cmd"]:
        # e.g., ["python", "-m", "agents.foo.bar"] → "bar"
        parts = list(spec["cmd"])
        try:
            if "-m" in parts:
                mod = parts[parts.index("-m") + 1]
                return mod.split(".")[-1]
        except Exception:
            pass
        # fallback to first arg
        return Path(parts[0]).name
    return "agent"

# ---------------- generic agent fixture ----------------

@pytest.fixture(scope="function")
def agents_up(request, transport_config):
    """
    Start one or more registered agents via @pytest.mark.agents([...]).
    Example:
        @pytest.mark.agents(["brazil-farm", "weather-mcp"])
        def test_things(agents_up): ...
    """
    m = request.node.get_closest_marker("agents")
    agent_names = (m.args[0] if m and m.args else m.kwargs.get("names", [])) if m else []

    runners: list[ProcessRunner] = []

    for name in agent_names:
        spec = AGENTS.get(name)
        if not spec:
            raise ValueError(f"Unknown agent: {name!r}. Add it to AGENTS dict.")

        env = _base_env()
        env.update(transport_config or {})

        print(f"\n--- Starting {name} ---")
        runner = ProcessRunner(
            name=name,
            cmd=spec["cmd"],
            cwd=str(CORTO_DIR),
            env=env,
            ready_pattern=spec.get("ready_pattern", r"Transport initialized with tracing enabled"),
            timeout_s=30.0,
            log_dir=Path(CORTO_DIR) / ".pytest-logs",
        ).start()
        _ACTIVE_RUNNERS.append(runner)

        try:
            runner.wait_ready()
        except TimeoutError:
            print(f"--- {name} logs: {runner.log_path}")
            runner.stop()
            raise

        print(f"--- {name} ready (logs: {runner.log_path}) ---")
        runners.append(runner)

    try:
        yield
    finally:
        for r in runners:
            print(f"--- Stopping {r.name} ---")
            r.stop()

# ---------------- client ----------------

@pytest.fixture
def supervisor_client(transport_config, monkeypatch):
    for k, v in _base_env().items():
        monkeypatch.setenv(k, str(v))
    for k, v in transport_config.items():
        monkeypatch.setenv(k, v)

    _purge_modules([
        "exchange",
        "config.config",
    ])

    import exchange.main as exchange_main
    import importlib
    importlib.reload(exchange_main)

    app = exchange_main.app
    with TestClient(app) as client:
        yield client
