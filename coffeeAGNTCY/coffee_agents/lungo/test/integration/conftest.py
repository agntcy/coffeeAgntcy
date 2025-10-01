"""
Sets up external integrations that are used in the CoffeeAGNTCY reference application.
"""
import time
import pytest
import sys
import os
from pathlib import Path
from xprocess import ProcessStarter

from fastapi.testclient import TestClient
from unittest.mock import patch

from agents.supervisors.auction.main import app as auction_app
# from coffee_agents.lungo.agents.supervisors.auction.graph import shared
# from coffee_agents.lungo.agents.supervisors.auction.graph.graph import ExchangeGraph
# from agents.supervisors.logistic.main import app as logistics_app
from test.integration.docker_helpers import up, down
from test.integration.mocks.mock_llm import MockLangChainLLM

LUNGO_DIR = Path(__file__).resolve().parents[2]  # coffee_agents/lungo

@pytest.fixture(scope="session", autouse=True)
def orchestrate_session_services():
    print("\n--- Setting up session level service integrations ---")
    setup_transports()
    # setup_observability()
    setup_identity()
    print("--- Session level service setup complete. Tests can now run ---")

    yield 

    # print("--- Tearing down integrations after test session ---")   
    # down(["docker-compose.yaml"])
    # print("--- Integrations torn down ---")

@pytest.fixture(autouse=True, scope="function")
def mock_llm_factory():
    # Patch the symbol where it's LOOKED UP: yourpkg.llm.LLMFactory
    with patch("common.llm.LLMFactory") as Factory:
        instance = Factory.return_value
        mock_llm = MockLangChainLLM("gpt-4o")
        mock_llm.set_mock_responses({
            "colombia": "Colombia farm inventory has 500 lb.",
            "vietnam": "Vietnam farm inventory has 100 lb.",
            "brazil": "Brazil farm inventory includes 20 lb.",
        })
        instance.get_llm.return_value = mock_llm
        yield mock_llm
        
@pytest.fixture(autouse=True, scope="session")
def disable_dotenv_load():
    """Prevent farm/server modules from loading `.env` during tests."""
    with patch("dotenv.load_dotenv", return_value=True):
        yield

@pytest.fixture(scope="session")
def transport_config(request):
    # default if not parametrized
    return getattr(request, "param")

@pytest.fixture(scope="session")
def brazil_farm_up(xprocess, transport_config):
    class BrazilStarter(ProcessStarter):
        pattern = r"Uvicorn running on http://0\.0\.0\.0:9999"
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
    pid, log = xprocess.ensure("brazil-farm", BrazilStarter)
    yield
    xprocess.getinfo("brazil-farm").terminate()

@pytest.fixture(scope="function")
def auction_supervisor_client(transport_config):
    """
    Provide a TestClient bound to the auction supervisor, with env matching the transport.
    Import the app after env is set so startup reads the right transport.
    """
    os.environ.update(transport_config)
    from agents.supervisors.auction.main import app as auction_app  # import after env is set
    with TestClient(auction_app) as client:
        yield client

def setup_transports():
    _startup_slim()
    _startup_nats()

def setup_observability():
    # _startup_otel_collector()
    # _startup_clickhouse()
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
    # wait a bit more for it to be ready
    time.sleep(10)

