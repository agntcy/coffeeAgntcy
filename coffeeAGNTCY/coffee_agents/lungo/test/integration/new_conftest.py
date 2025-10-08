# from contextlib import contextmanager
# import importlib
# import logging
# import os
# import subprocess
# from pathlib import Path
# import sys
# import time
# from typing import Dict, List, Tuple

# import pytest
# from fastapi.testclient import TestClient
# from testcontainers.compose import DockerCompose

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# ROOT = Path(__file__).resolve().parents[2]
# COMPOSE_FILE = "docker-compose.yaml"
# PROJECT = "coffee_tests"

# FARMS = ["brazil", "colombia", "vietnam"]
# FARM_SERVICE = lambda name: f"{name}-farm-server"
# WEATHER_SERVICE = "weather-mcp-server"
# FARM_PORT = {"brazil": 9999, "colombia": 9998, "vietnam": 9997}

# # ---------- Helpers ----------

# def _dc(*args: str) -> None:
#     """Run docker compose with our project/file."""
#     subprocess.run(
#         ["docker", "compose", "-f", str(ROOT / COMPOSE_FILE), *args],
#         check=True,
#     )

# @contextmanager
# def env_vars(d: Dict[str, str]):
#     old = {k: os.environ.get(k) for k in d}
#     os.environ.update({k: str(v) for k, v in d.items()})
#     try:
#         yield
#     finally:
#         for k, v in old.items():
#             if v is None:
#                 os.environ.pop(k, None)
#             else:
#                 os.environ[k] = v

# def wait_for_log(service: str, needle: str, timeout: float = 60):
#     start = time.time()
#     while time.time() - start < timeout:
#         logs = subprocess.run(
#             ["docker", "compose", "-f", str(COMPOSE_FILE), "--project-name", PROJECT, "logs", service],
#             capture_output=True, text=True, check=False
#         ).stdout
#         if needle in logs:
#             return
#         time.sleep(0.5)
#     raise TimeoutError(f"{service} did not emit '{needle}' within {timeout}s")


# # ---------- Per-session fixtures ----------

# @pytest.fixture(scope="session", autouse=True)
# def session_transports():
#     logging.info("\n--- Starting transport services for test session ---")
#     with env_vars({"COMPOSE_PROFILES": "transports"}):
#         compose = DockerCompose(str(ROOT), compose_file_name=COMPOSE_FILE, build=True)
#         compose.start()
#         yield
#     compose.stop()

# @pytest.fixture(scope="session", autouse=True)
# def session_observability():
#     logging.info("\n--- Starting observability services for test session ---")
#     with env_vars({"COMPOSE_PROFILES": "observability"}):
#         compose = DockerCompose(str(ROOT), compose_file_name=COMPOSE_FILE, build=True)
#         compose.start()
#         yield
#     compose.stop()

# # ---------- Per-test fixtures ----------

# @pytest.fixture(scope="session", autouse=True)
# def session_build_images():
#     """
#     Build all farm + service images once per test session.
#     This uses Docker's layer cache, so subsequent runs are fast.
#     """
#     logging.info("\n--- Building farm and service images once for test session ---")
#     farm_services = [f"{f}-farm-server" for f in FARMS]
#     services_to_build = farm_services + [WEATHER_SERVICE]
#     _dc("build", *services_to_build)

#     logging.info(f"--- Built images: {', '.join(services_to_build)} ---")
#     yield


# @pytest.fixture(scope="function")
# def farm_selection(request) -> List[str]:
#     """Use @pytest.mark.farms(['brazil', 'colombia']) to choose farms per test."""
#     m = request.node.get_closest_marker("farms")
#     if not m:
#         return []
#     names = m.args[0] if m.args else m.kwargs.get("names", [])
#     return [n for n in names if n in FARMS]

# @pytest.fixture(scope="function")
# def transport_config(request) -> Dict[str, str]:
#     # picked up from your @pytest.mark.parametrize(..., indirect=True)
#     return dict(getattr(request, "param", {}) or {})

# @pytest.fixture(scope="function")
# def farms_up(farm_selection, transport_config):
#     """
#     Start only the selected farm services; tear them down after the test.
#     Infra is already up at session scope.
#     """
#     if not farm_selection:
#         yield {}
#         return

#     # Up just these services (build on first use; cached afterward).
#     services = [FARM_SERVICE(f) for f in farm_selection]
#     with env_vars({**transport_config}):
#         _dc("up", "-d", "--build", *services)

#     # wait for the log line per service (simple and robust)
#     for svc in services:
#         wait_for_log(svc, "Message bridge started.", timeout=90)

#     # # Use DockerCompose for convenient port lookup.
#     # compose = DockerCompose(str(ROOT), compose_file_name=COMPOSE_FILE,
#     #                         build=False)

#     # endpoints: Dict[str, Tuple[str, int]] = {}
#     # for farm in farm_selection:
#     #     svc = FARM_SERVICE(farm)
#     #     host_port = int(compose.get_service_port(svc, FARM_PORT[farm]))
#     #     endpoints[farm] = ("localhost", host_port)

#     try:
#         # yield endpoints
#         yield
#     finally:
#         # Stop & remove only these services; keep session infra alive.
#         _dc("stop", *services)
#         _dc("rm", "-f", *services)

# @pytest.fixture(scope="function")
# def start_weather_mcp(transport_config):
#     """
#     Opt-in weather MCP per test (no profile needed).
#     """
#     with env_vars({**transport_config}):
#         _dc("up", "-d", "--build", WEATHER_SERVICE)
#     try:
#         yield True
#     finally:
#         _dc("stop", WEATHER_SERVICE)
#         _dc("rm", "-f", WEATHER_SERVICE)

# # ---------- Supervisor client (unchanged) ----------

# def _purge_modules(prefixes):
#     to_delete = [m for m in list(sys.modules)
#                  if any(m == p or m.startswith(p + ".") for p in prefixes)]
#     for m in to_delete:
#         sys.modules.pop(m, None)

# @pytest.fixture
# def auction_supervisor_client(transport_config, monkeypatch):
#     for k, v in transport_config.items():
#         monkeypatch.setenv(k, v)

#     # clear any cached modules
#     _purge_modules([
#     "agents.supervisors.auction",
#     "config.config",              
#     ])

#     import agents.supervisors.auction.main as auction_main
#     # force reload to pick up env changes
#     importlib.reload(auction_main)

#     app = auction_main.app
#     with TestClient(app) as client:
#         yield client
