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

LUNGO_DIR = Path(__file__).resolve().parents[2]  # coffee_agents/lungo
FARMS = ["brazil", "colombia", "vietnam"]
# If HTTP is enabled, give each farm its own port (adjust to your servers)
PORTS = {"brazil": 9999, "colombia": 9998, "vietnam": 9997}

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
    # default if not parametrized
    return getattr(request, "param")

def _make_farm_starter(farm: str, env: dict, port: int | None):
    farm_path = "agents.farms." + farm + ".farm_server"

    class Starter(ProcessStarter):
        pattern = rf"Uvicorn running on http://0\.0\.0\.0:{port}" if port else r"Starting farm server"
        timeout = 30
        args = ["python", "-m", str(farm_path)]
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
        port = PORTS.get(farm, 0)
        env = {
            **os.environ,
            "PYTHONPATH": str(LUNGO_DIR) + (os.pathsep + os.environ.get("PYTHONPATH", "")),
            "ENABLE_HTTP": "true",
            "FARM_BROADCAST_TOPIC": "test-broadcast",
            **(transport_config or {}),
        }
        if env.get("ENABLE_HTTP", "true").lower() == "true":
            env["FARM_HTTP_PORT"] = str(port)

        Starter = _make_farm_starter(farm, env, port)
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
                pass


@pytest.fixture(scope="function")
def farm_up(request, xprocess, transport_config):
    farm = request.param  # e.g. "brazil", "colombia", "vietnam"
    proc_name = f"{farm}-farm"

    Starter = _make_farm_starter(farm, transport_config)

    # kill any stale instance with the same name so new env applies
    try:
        xprocess.getinfo(proc_name).terminate()
    except Exception:
        pass

    _, _ = xprocess.ensure(proc_name, Starter)
    try:
        yield
    finally:
        xprocess.getinfo(proc_name).terminate()

@pytest.fixture
def auction_supervisor_client(transport_config, monkeypatch):
    for k, v in transport_config.items():
        monkeypatch.setenv(k, v)

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

