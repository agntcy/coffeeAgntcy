# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Pytest fixtures using the simple ProcessRunner.
Replace prior xprocess usage with these.
"""
import atexit
import os
from urllib.parse import urlparse

# Force OTel SDK on in tests so we get recording spans; without this NonRecordingSpan would be created (from disabled SDK) which has no .attributes.
os.environ["OTEL_SDK_DISABLED"] = "false"
os.environ.setdefault("OTLP_HTTP_ENDPOINT", "http://127.0.0.1:4318")
# Required by docker-compose interpolation for several services (compose config during up/down).
os.environ.setdefault("WORKFLOW_API_KEY", "TheAnswerIs42")

import re
import time
import sys
import pytest
from pathlib import Path

from fastapi.testclient import TestClient
from tests.integration.docker_helpers import (
    up,
    down,
    remove_container_if_exists,
    ensure_compose_profile,
    wait_for_tcp_port,
)

from tests.integration.process_helper import ProcessRunner
import config.config # noqa: F401 # Note: imports config.config to set environment variables.

LUNGO_DIR = Path(__file__).resolve().parents[2]

# Observability stack services (otel-collector, clickhouse, grafana) use the compose profile.
ensure_compose_profile("observability")

_otel_shutdown_done = False

AGENT_POST_READY_SETTLE_SECS = 1.0

AGENTS = {
    # auction agents
    "brazil-farm": {
        "cmd": ["python", "-m", "agents.farms.brazil.farm_server", "--no-reload"],
        "ready_pattern": r"Agent ready",
    },
    "colombia-farm": {
        "cmd": ["python", "-m", "agents.farms.colombia.farm_server", "--no-reload"],
        "ready_pattern": r"Agent ready",
    },
    "vietnam-farm": {
        "cmd": ["python", "-m", "agents.farms.vietnam.farm_server", "--no-reload"],
        "ready_pattern": r"Agent ready",
    },
    "weather-mcp": {
        "cmd": ["uv", "run", "-m", "agents.mcp_servers.weather_service"],
        "ready_pattern": r"Agent ready",
    },
    # logistics agents
    "logistics-farm": {
        "cmd": ["python", "-m", "agents.logistics.farm.server", "--no-reload"],
        "ready_pattern": r"Agent ready",
    },
    "accountant": {
        "cmd": ["python", "-m", "agents.logistics.accountant.server", "--no-reload"],
        "ready_pattern": r"Agent ready",
    },
    "shipper": {
        "cmd": ["python", "-m", "agents.logistics.shipper.server", "--no-reload"],
        "ready_pattern": r"Agent ready",
    },
    "helpdesk": {
        "cmd": ["python", "-m", "agents.logistics.helpdesk.server", "--no-reload"],
        "ready_pattern": r"Agent ready",
    }
}

# ---------------- utils ----------------

def _base_env():
    # Use test env: SDK on so spans are recording (avoids NonRecordingSpan.attributes error).
    #
    # Agents run as host subprocesses but Docker Compose .env often uses service hostnames
    # (slim, nats). Those do not resolve on the host, so A2A startup never reaches "Agent ready".
    # Force loopback to match published compose ports (slim 46357, nats 4222).
    return {
        **os.environ,
        "PYTHONPATH": str(LUNGO_DIR),
        "FARM_BROADCAST_TOPIC": "farm_broadcast",
        "OTEL_SDK_DISABLED": os.environ.get("OTEL_SDK_DISABLED", "false"),
        "OTLP_HTTP_ENDPOINT": os.environ.get("OTLP_HTTP_ENDPOINT", "http://127.0.0.1:4318"),
        "PYTHONUNBUFFERED": "1",
        "PYTHONFAULTHANDLER": "1",
        "TRANSPORT_SERVER_ENDPOINT": os.environ.get(
            "TRANSPORT_SERVER_ENDPOINT", "http://127.0.0.1:46357"
        ),
        "SLIM_SERVER": "127.0.0.1:46357",
        "NATS_SERVER": "127.0.0.1:4222",
    }

def _purge_modules(prefixes, keep=None):
    keep = set(keep or [])
    to_delete = [m for m in list(sys.modules)
                 if any(m == p or m.startswith(p + ".") for p in prefixes)
                 and m not in keep
                 and not any(m.startswith(k + ".") for k in keep)]
    for m in to_delete:
        sys.modules.pop(m, None)


def _save_modules(prefixes):
    """Return a dict of module name -> module for all modules matching prefixes."""
    return {
        m: sys.modules[m]
        for m in list(sys.modules)
        if any(m == p or m.startswith(p + ".") for p in prefixes)
    }


def _restore_modules(saved):
    """Put saved modules back into sys.modules so other tests see the same state."""
    for name, mod in saved.items():
        sys.modules[name] = mod


def _wait_ready(client, path, timeout_s=30.0, poll_s=0.5):
    """Poll GET path until status 200 or timeout."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        resp = client.get(path)
        if resp.status_code == 200:
            return
        time.sleep(poll_s)
    raise RuntimeError(f"Ready check {path} did not return 200 within {timeout_s}s")

# ---------------- session infra ----------------
# docker_helpers passes env=os.environ to compose so infra containers use the same env as the test (e.g. OTEL_SDK_DISABLED).
files = ["docker-compose.yaml"]
if Path("docker-compose.override.yaml").exists():
    files.append("docker-compose.override.yaml")

_session_docker_torn_down = False


def _teardown_session_docker():
    """Run docker compose down so session containers (slim, nats, grafana, etc.) are stopped. Idempotent."""
    global _session_docker_torn_down
    if _session_docker_torn_down:
        return
    _session_docker_torn_down = True
    print("--- Tearing down session Docker (slim, nats, otel-collector, clickhouse, grafana) ---")
    down(files)


def _shutdown_otel_sdk():
    """Flush and shutdown OTEL/ioa_observe in this process before the collector stops.

    Metrics export uses a background thread; shut it down while localhost:4318 is still up.
    ioa_observe registers its own atexit flush — call this before ``docker compose down``.
    """
    global _otel_shutdown_done
    if _otel_shutdown_done:
        return
    _otel_shutdown_done = True

    timeout_millis = 30_000
    try:
        from opentelemetry import metrics, trace

        mp = metrics.get_meter_provider()
        if hasattr(mp, "force_flush"):
            mp.force_flush(timeout_millis=timeout_millis)
        if hasattr(mp, "shutdown"):
            mp.shutdown(timeout_millis=timeout_millis)

        try:
            from ioa_observe.sdk.tracing.tracing import TracerWrapper

            if getattr(TracerWrapper, "endpoint", None) and hasattr(TracerWrapper, "instance"):
                TracerWrapper.instance.flush()
        except Exception:  # noqa: BLE001
            pass

        tp = trace.get_tracer_provider()
        if hasattr(tp, "force_flush"):
            tp.force_flush(timeout_millis=timeout_millis)
        if hasattr(tp, "shutdown"):
            tp.shutdown()
    except Exception:  # noqa: BLE001
        pass


# atexit is LIFO: register docker first so OTEL shutdown runs before compose down on abrupt exit.
atexit.register(_teardown_session_docker)
atexit.register(_shutdown_otel_sdk)


@pytest.fixture(scope="session", autouse=True)
def orchestrate_session_services():
    print("\n--- Setting up session level service integrations ---")
    down(files)
    remove_container_if_exists("lungo-slim")
    remove_container_if_exists("lungo-nats")
    remove_container_if_exists("lungo-otel-collector")
    remove_container_if_exists("lungo-clickhouse-server")
    remove_container_if_exists("grafana-lungo")
    setup_transports()
    setup_observability()
    setup_identity()
    print("--- Session level service setup complete. Tests can now run ---")
    yield
    _shutdown_otel_sdk()
    try:
        from huggingface_hub.utils import close_session

        close_session()
    except Exception:
        pass
    # Docker teardown runs from atexit after all OTEL/ioa_observe atexit hooks finish.

def setup_transports():
    _startup_slim()
    _startup_nats()

def setup_observability():
    _startup_clickhouse()
    _startup_otel_collector()
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

def _otlp_host_port() -> tuple[str, int]:
    parsed = urlparse(os.environ.get("OTLP_HTTP_ENDPOINT", "http://127.0.0.1:4318"))
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 4318
    return host, port


def _wait_otlp_http_endpoint(timeout_s: float = 120.0) -> None:
    host, port = _otlp_host_port()
    print(f"--- Waiting for OTLP HTTP endpoint {host}:{port} ---")
    wait_for_tcp_port(host, port, timeout_s=timeout_s)


def _startup_otel_collector():
    up(files, ["otel-collector"])
    _wait_otlp_http_endpoint()

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
                "ready_pattern": "Agent ready",
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

        Farm agents (e.g. brazil-farm, colombia-farm, vietnam-farm) are started as
        local Python subprocesses (ProcessRunner), not as Docker services. Docker
        is used only for session-level infra: slim, nats, otel-collector,
        clickhouse-server, grafana. Each agent runs with env = _base_env() |
        transport_config (so it inherits the test run's environment, including
        LLM/LiteLLM vars if set). ``_base_env`` forces ``SLIM_SERVER`` and
        ``NATS_SERVER`` to loopback so subprocesses can reach published compose ports
        even when the shell ``.env`` uses Docker service hostnames.

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
            cwd=str(LUNGO_DIR),
            env=env,
            ready_pattern=spec.get("ready_pattern", r"Agent ready"),
            timeout_s=60.0,
            log_dir=Path(LUNGO_DIR) / ".pytest-logs",
        ).start()

        try:
            runner.wait_ready()
        except TimeoutError:
            print(f"--- {name} logs: {runner.log_path}")
            runner.stop()
            raise

        print(f"--- {name} ready (logs: {runner.log_path}) ---")
        runners.append(runner)

    # Wait for the agents to settle after they are ready (might need some time to properly answer even when ready)
    if runners:
        time.sleep(AGENT_POST_READY_SETTLE_SECS)

    try:
        yield
    finally:
        for r in reversed(runners):
            print(f"--- Stopping {r.name} ---")
            r.stop()

# ---------------- http client ----------------

@pytest.fixture
def auction_supervisor_client(transport_config, monkeypatch):
    for k, v in _base_env().items():
        monkeypatch.setenv(k, str(v))
    for k, v in transport_config.items():
        monkeypatch.setenv(k, v)

    prefixes = ["agents.supervisors.auction", "config.config"]
    # Keep the shared module (holds A2AClientFactory + SLIM connections) alive
    # across tests — the SLIM native runtime rejects duplicate connections to
    # the same endpoint, so recreating the factory per-test causes
    # "client already connected" errors.
    keep = ["agents.supervisors.auction.graph.shared"]
    saved = _save_modules(prefixes)
    try:
        _purge_modules(prefixes, keep=keep)

        import agents.supervisors.auction.main as auction_main
        import importlib
        importlib.reload(auction_main)

        app = auction_main.app
        with TestClient(app) as client:
            _wait_ready(client, "/ready")
            yield client
    finally:
        _purge_modules(prefixes, keep=keep)
        _restore_modules(saved)

@pytest.fixture
def logistics_supervisor_client(transport_config, monkeypatch):
    for k, v in _base_env().items():
        monkeypatch.setenv(k, str(v))
    for k, v in transport_config.items():
        monkeypatch.setenv(k, v)

    prefixes = ["agents.supervisors.logistics", "config.config"]
    saved = _save_modules(prefixes)
    try:
        _purge_modules(prefixes)

        import agents.supervisors.logistics.main as logistics_main
        import importlib
        importlib.reload(logistics_main)

        app = logistics_main.app
        with TestClient(app) as client:
            _wait_ready(client, "/v1/health")
            yield client
    finally:
        _purge_modules(prefixes)
        _restore_modules(saved)

@pytest.fixture
def helpdesk_client(transport_config, monkeypatch):
    for k, v in _base_env().items():
        monkeypatch.setenv(k, str(v))
    for k, v in transport_config.items():
        monkeypatch.setenv(k, v)

    prefixes = ["agents.logistics.helpdesk", "config.config"]
    saved = _save_modules(prefixes)
    try:
        _purge_modules(prefixes)

        import importlib
        import agents.logistics.helpdesk.server as helpdesk_server
        importlib.reload(helpdesk_server)

        from fastapi.testclient import TestClient
        app = helpdesk_server.app
        with TestClient(app) as client:
            yield client
    finally:
        _purge_modules(prefixes)
        _restore_modules(saved)

@pytest.fixture
def logistics_shipper_client(transport_config, monkeypatch):
    for k, v in _base_env().items():
        monkeypatch.setenv(k, str(v))
    for k, v in transport_config.items():
        monkeypatch.setenv(k, v)

    prefixes = ["agents.logistics.shipper", "config.config"]
    saved = _save_modules(prefixes)
    try:
        _purge_modules(prefixes)

        import importlib
        import agents.logistics.shipper.server as shipper_server
        importlib.reload(shipper_server)

        from fastapi.testclient import TestClient
        app = shipper_server.app
        with TestClient(app) as client:
            yield client
    finally:
        _purge_modules(prefixes)
        _restore_modules(saved)

@pytest.fixture
def logistics_farm_client(transport_config, monkeypatch):
    for k, v in _base_env().items():
        monkeypatch.setenv(k, str(v))
    for k, v in transport_config.items():
        monkeypatch.setenv(k, v)

    prefixes = ["agents.logistics.farm", "config.config"]
    saved = _save_modules(prefixes)
    try:
        _purge_modules(prefixes)

        import importlib
        import agents.logistics.farm.server as farm_server
        importlib.reload(farm_server)

        from fastapi.testclient import TestClient
        app = farm_server.app
        with TestClient(app) as client:
            yield client
    finally:
        _purge_modules(prefixes)
        _restore_modules(saved)

@pytest.fixture
def logistics_accountant_client(transport_config, monkeypatch):
    for k, v in _base_env().items():
        monkeypatch.setenv(k, str(v))
    for k, v in transport_config.items():
        monkeypatch.setenv(k, v)

    prefixes = ["agents.logistics.accountant", "config.config"]
    saved = _save_modules(prefixes)
    try:
        _purge_modules(prefixes)

        import importlib
        import agents.logistics.accountant.server as accountant_server
        importlib.reload(accountant_server)

        from fastapi.testclient import TestClient
        app = accountant_server.app
        with TestClient(app) as client:
            yield client
    finally:
        _purge_modules(prefixes)
        _restore_modules(saved)


def pytest_sessionfinish(session, exitstatus) -> None:  # noqa: ARG001
    _shutdown_otel_sdk()
