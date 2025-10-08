"""
Sets up external integrations that are used in the CoffeeAGNTCY reference application.
"""

import importlib
import time
import pytest
import sys
import os
from pathlib import Path
from xprocess import ProcessStarter

from fastapi.testclient import TestClient
from test.integration.docker_helpers import up, down


LUNGO_DIR = Path(__file__).resolve().parents[2]
FARMS = ["brazil", "colombia", "vietnam"]

def _base_env():
    return {
        **os.environ,
        "PYTHONPATH": str(LUNGO_DIR),
        "ENABLE_HTTP": "true",
        "FARM_BROADCAST_TOPIC": "test-broadcast",
        "PYTHONUNBUFFERED": "1",
        "PYTHONFAULTHANDLER": "1",
    }

@pytest.fixture(scope="session", autouse=True)
def orchestrate_session_services():
    print("\n--- Setting up session level service integrations ---")
    setup_transports()
    setup_observability()
    setup_identity()
    print("--- Session level service setup complete. Tests can now run ---")

    yield 

    # print("--- Tearing down integrations after test session ---")   
    # down(["docker-compose.yaml"])
    # print("--- Integrations torn down ---")

def _purge_modules(prefixes):
    to_delete = [m for m in list(sys.modules)
                 if any(m == p or m.startswith(p + ".") for p in prefixes)]
    for m in to_delete:
        sys.modules.pop(m, None)

@pytest.fixture(scope="function")
def transport_config(request):
    return dict(getattr(request, "param", {}) or {})

def _make_farm_starter(farm: str, env: dict):
    farm_path = "agents.farms." + farm + ".farm_server"

    class Starter(ProcessStarter):
        pattern = "Started server process"
        timeout = 30
        terminate_on_interrupt = True
        args = ["python", "-m", str(farm_path), "--no-reload"]
        cwd = str(LUNGO_DIR)
    
    Starter.env = env
    return Starter

@pytest.fixture(scope="function")
def farm_selection(request):
    """Per-test farm selection via @pytest.mark.farms([...])"""
    m = request.node.get_closest_marker("farms")
    if not m:
        return []
    names = m.args[0] if m.args else m.kwargs.get("names", [])
    return [f for f in names if f in FARMS]

@pytest.fixture(scope="function")
def farms_up(farm_selection, xprocess, transport_config):
    """Start the selected farms for this test, then tear them down."""
    proc_names = []

    for farm in farm_selection:
        print(f"\n--- Starting farm {farm} ---")
        env = _base_env()
        env.update(transport_config or {})
        Starter = _make_farm_starter(farm, env)
        proc_name = f"{farm}-farm"

        try:
            xprocess.getinfo(proc_name).terminate()
        except Exception:
            pass
        xprocess.ensure(proc_name, Starter)
        proc_names.append(proc_name)

    try:
        yield
    finally:
        for name in proc_names:
            try:
                xprocess.getinfo(name).terminate()
            except Exception:
                print(f"--- Could not terminate process {name} ---")

@pytest.fixture(scope="function")
def start_weather_mcp(xprocess, transport_config):
    env = _base_env()
    env.update(transport_config or {})

    class Starter(ProcessStarter):
        pattern = "Starting weather service"
        timeout = 30
        terminate_on_interrupt = True
        args = ["uv", "run", "-m", "agents.mcp_servers.weather_service"]
        cwd = str(LUNGO_DIR)

    Starter.env = env
    proc_name = "weather-mcp-server"
    # ensure clean slate
    try:
        xprocess.getinfo(proc_name).terminate()
    except Exception:
        pass

    xprocess.ensure(proc_name, Starter)

    try:
        yield
    finally:
        try:
            xprocess.getinfo(proc_name).terminate()
        except Exception:
            pass

@pytest.fixture
def auction_supervisor_client(transport_config, monkeypatch):
    for k, v in transport_config.items():
        monkeypatch.setenv(k, v)

    # clear any cached modules
    _purge_modules([
    "agents.supervisors.auction",
    "config.config",              
    ])

    import agents.supervisors.auction.main as auction_main
    # force reload to pick up env changes
    importlib.reload(auction_main)

    app = auction_main.app
    with TestClient(app) as client:
        yield client

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


