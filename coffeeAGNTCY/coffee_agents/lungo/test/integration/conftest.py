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
# from unittest.mock import patch

# from agents.supervisors.auction.main import app as auction_app
# from coffee_agents.lungo.agents.supervisors.auction.graph import shared
# from coffee_agents.lungo.agents.supervisors.auction.graph.graph import ExchangeGraph
# from agents.supervisors.logistic.main import app as logistics_app
from test.integration.docker_helpers import up, down
# from test.integration.mocks.mock_llm import MockLangChainLLM

LUNGO_DIR = Path(__file__).resolve().parents[2]  # coffee_agents/lungo

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

# @pytest.fixture(autouse=True, scope="function")
# def mock_llm_factory():
#     # Patch the symbol where it's LOOKED UP: yourpkg.llm.LLMFactory
#     with patch("common.llm.LLMFactory") as Factory:
#         instance = Factory.return_value
#         mock_llm = MockLangChainLLM("gpt-4o")
#         mock_llm.set_mock_responses({
#             "colombia": "Colombia farm inventory has 500 lb.",
#             "vietnam": "Vietnam farm inventory has 100 lb.",
#             "brazil": "Brazil farm inventory includes 20 lb.",
#         })
#         instance.get_llm.return_value = mock_llm
#         yield mock_llm
        
# @pytest.fixture(autouse=True, scope="session")
# def disable_dotenv_load():
#     """Prevent farm/server modules from loading `.env` during tests."""
#     with patch("dotenv.load_dotenv", return_value=True):
#         yield

def _purge_modules(prefixes):
    to_delete = [m for m in list(sys.modules)
                 if any(m == p or m.startswith(p + ".") for p in prefixes)]
    for m in to_delete:
        sys.modules.pop(m, None)

@pytest.fixture(scope="function")
def transport_config(request):
    # default if not parametrized
    return getattr(request, "param")

def _make_farm_starter(farm: str, transport_config: dict):
    farm_path = LUNGO_DIR / "agents" / "farms" / farm / "farm_server.py"

    class Starter(ProcessStarter):
        # Match a startup line that appears regardless of HTTP
        pattern = r"Starting farm server with transport .*"
        timeout = 30
        args = ["python", "-u", str(farm_path)]
        cwd = str(LUNGO_DIR)
        env = {
            **os.environ,
            "PYTHONPATH": str(LUNGO_DIR)
                + (os.pathsep + os.environ.get("PYTHONPATH", "")),
            "ENABLE_HTTP": "false",              # <— avoid port conflicts
            "FARM_BROADCAST_TOPIC": "test-broadcast",
            **(transport_config or {}),
        }
    return Starter

@pytest.fixture(scope="function")
def all_farms_up(xprocess, transport_config):
    """Start all farms concurrently; stop them after the test."""
    proc_names = []
    tr = (transport_config or {}).get("DEFAULT_MESSAGE_TRANSPORT", "unknown").lower()

    for farm in FARMS:
        name = f"{farm}-farm-{tr}"
        proc_names.append(name)
        Starter = _make_farm_starter(farm, transport_config)

        # kill any stale process with same name/env combo
        try:
            xprocess.getinfo(name).terminate()
        except Exception:
            pass

        xprocess.ensure(name, Starter)

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

@pytest.fixture(scope="function")
def brazil_farm_up(xprocess, transport_config):
    class BrazilStarter(ProcessStarter):
        timeout = 30
        args = [
            "python", "-u",
            str(LUNGO_DIR / "agents" / "farms" / "brazil" / "farm_server.py"),
        ]
        cwd = str(LUNGO_DIR)
        env = {
            **os.environ,
            "PYTHONPATH": str(LUNGO_DIR) + (os.pathsep + os.environ.get("PYTHONPATH","")),
            "ENABLE_HTTP": "true",
            "FARM_BROADCAST_TOPIC": "test-broadcast",
            **transport_config,
        }
        
    # in case a stale process is around:
    try:
        xprocess.getinfo("brazil-farm").terminate()
    except Exception:
        pass

    _, _ = xprocess.ensure("brazil-farm", BrazilStarter)
    yield
    xprocess.getinfo("brazil-farm").terminate()

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

