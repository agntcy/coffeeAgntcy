"""
Pytest fixtures using the simple ProcessRunner.
Replace prior xprocess usage with these.
"""
import atexit
import importlib
import os
import time
import sys
import pytest
from pathlib import Path

from fastapi.testclient import TestClient
from test.integration.docker_helpers import up, down

from test.integration.process_helper import ProcessRunner 

LUNGO_DIR = Path(__file__).resolve().parents[2]
FARMS = ["brazil", "colombia", "vietnam", "logistics"]
_ACTIVE_RUNNERS = []

# ---------------- utils ----------------

def _base_env():
    return {
        **os.environ,
        "PYTHONPATH": str(LUNGO_DIR),
        "ENABLE_HTTP": "true",
        "FARM_BROADCAST_TOPIC": "test-broadcast",
        "PYTHONUNBUFFERED": "1",
        "PYTHONFAULTHANDLER": "1",
    }

def _purge_modules(prefixes):
    to_delete = [m for m in list(sys.modules)
                 if any(m == p or m.startswith(p + ".") for p in prefixes)]
    for m in to_delete:
        sys.modules.pop(m, None)

def _farm_cmd(farm: str) -> list[str]:
    # python -m agents.farms.<farm>.farm_server --no-reload
    return ["python", "-m", f"agents.farms.{farm}.farm_server", "--no-reload"]

# ---------------- session infra ----------------

@pytest.fixture(scope="session", autouse=True)
def orchestrate_session_services():
    print("\n--- Setting up session level service integrations ---")
    setup_transports()
    setup_observability()
    setup_identity()
    print("--- Session level service setup complete. Tests can now run ---")
    yield
    #Uncomment if you want to bring down infra after tests:
    down(["docker-compose.yaml"])

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
    up(["docker-compose.yaml"], ["slim"])

def _startup_nats():
    up(["docker-compose.yaml"], ["nats"])

def _startup_grafana():
    up(["docker-compose.yaml"], ["grafana"])

def _startup_clickhouse():
    up(["docker-compose.yaml"], ["clickhouse-server"])

def _startup_otel_collector():
    up(["docker-compose.yaml"], ["otel-collector"])
    time.sleep(10)

# ---------------- per-test config ----------------

@pytest.fixture(scope="function")
def transport_config(request):
    return dict(getattr(request, "param", {}) or {})

@pytest.fixture(scope="function")
def farm_selection(request):
    """Select farms via @pytest.mark.farms([...])"""
    m = request.node.get_closest_marker("farms")
    if not m:
        return []
    names = m.args[0] if m.args else m.kwargs.get("names", [])
    return [f for f in names if f in FARMS]

# ---------------- farm + mcp fixtures ----------------

@pytest.fixture(scope="function")
def farms_up(farm_selection, transport_config):
    """
    Start selected farms for this test, stream logs with prefixes, then tear down.
    """
    runners: list[ProcessRunner] = []

    for farm in farm_selection:
        name = f"{farm}-farm"
        env = _base_env()
        env.update(transport_config or {})

        print(f"\n--- Starting {name} ---")
        runner = ProcessRunner(
            name=name,
            cmd=_farm_cmd(farm),
            cwd=str(LUNGO_DIR),
            env=env,
            ready_pattern=r"Started server process",
            timeout_s=30.0,
            log_dir=Path(LUNGO_DIR) / ".pytest-logs",
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

@pytest.fixture(scope="function")
def start_weather_mcp(transport_config):
    env = _base_env()
    env.update(transport_config or {})

    print("\n--- Starting weather-mcp-server ---")
    runner = ProcessRunner(
        name="weather-mcp-server",
        cmd=["uv", "run", "-m", "agents.mcp_servers.weather_service"],
        cwd=str(LUNGO_DIR),
        env=env,
        ready_pattern=r"Starting weather service",
        timeout_s=30.0,
        log_dir=Path(LUNGO_DIR) / ".pytest-logs",
    ).start()
    _ACTIVE_RUNNERS.append(runner)

    try:
        runner.wait_ready()
    except TimeoutError:
        print(f"--- weather-mcp-server logs: {runner.log_path}")
        runner.stop()
        raise

    print(f"--- weather-mcp-server ready (logs: {runner.log_path}) ---")
    try:
        yield
    finally:
        print("--- Stopping weather-mcp-server ---")
        runner.stop()

# ---------------- http client ----------------

@pytest.fixture
def auction_supervisor_client(transport_config, monkeypatch):
    for k, v in transport_config.items():
        monkeypatch.setenv(k, v)

    _purge_modules([
        "agents.supervisors.auction",
        "config.config",
    ])

    import agents.supervisors.auction.main as auction_main
    import importlib
    importlib.reload(auction_main)

    app = auction_main.app
    with TestClient(app) as client:
        yield client

@atexit.register
def _kill_any_leftover_runners():
    for r in _ACTIVE_RUNNERS:
        try:
            r.stop()
        except Exception:
            pass
