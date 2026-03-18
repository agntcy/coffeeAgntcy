# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import atexit
import os
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import time

import httpx
import pytest
from dotenv import load_dotenv
from pathlib import Path

from test.integration.docker_helpers import up, down, remove_container_if_exists

load_dotenv()

RECRUITER_DIR = Path(__file__).resolve().parents[2]

# ---------------- Ensure DIRCTL is available ----------------
DIRCTL_VERSION = "v1.0.0"
BIN_DIR = RECRUITER_DIR / "bin"
LOCAL_DIRCTL = BIN_DIR / "dirctl"


def _dirctl_download_suffix() -> str:
    """Return the dir release asset suffix, e.g. linux-amd64 (matches Dockerfile naming)."""
    if sys.platform not in ("linux", "darwin"):
        raise RuntimeError(
            f"Unsupported OS for automatic dirctl download: {sys.platform!r}. "
            "Only linux and darwin are supported; install dirctl manually."
        )
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        arch = "amd64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        raise RuntimeError(
            f"Unsupported CPU architecture for dirctl: {machine!r}. "
            "Install dirctl manually and make sure it is on PATH."
        )
    return f"{sys.platform}-{arch}"


def _path_is_executable(path: Path) -> bool:
    """Check if a path is a file and executable."""
    return path.is_file() and os.access(path, os.X_OK)


def _find_executable_on_path(cmd: str) -> str | None:
    location = shutil.which(cmd)
    if location and os.access(location, os.X_OK):
        return location
    return None


def _download_dirctl(dest: Path) -> None:
    """Download dirctl from the pinned GitHub release (streaming, sync httpx)."""
    suffix = _dirctl_download_suffix()
    url = (
        f"https://github.com/agntcy/dir/releases/download/"
        f"{DIRCTL_VERSION}/dirctl-{suffix}"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                with tmp.open("wb") as f:
                    for chunk in resp.iter_bytes():
                        f.write(chunk)
        if dest.exists():
            dest.unlink()
        tmp.replace(dest)
    except (httpx.HTTPError, OSError) as e:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to download dirctl from {url}: {e}") from e
    mode = dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    dest.chmod(mode)


@pytest.fixture(scope="session", autouse=True)
def ensure_dirctl():
    """Ensure dirctl is available: use PATH, else reuse `recruiter/bin/dirctl`, else download.

    Prepends recruiter/bin to PATH when using the downloaded binary so subprocess calls to `dirctl` work.
    """
    if _find_executable_on_path("dirctl"):
        return
    if _path_is_executable(LOCAL_DIRCTL):
        os.environ["PATH"] = f"{BIN_DIR}{os.pathsep}{os.environ.get('PATH', '')}"
        return
    _download_dirctl(LOCAL_DIRCTL)
    os.environ["PATH"] = f"{BIN_DIR}{os.pathsep}{os.environ.get('PATH', '')}"


@pytest.fixture(scope="session")
def dirctl_path(ensure_dirctl) -> Path:
    """Absolute path to the dirctl binary after :func:`ensure_dirctl` runs."""
    p = shutil.which("dirctl")
    if not p:
        raise RuntimeError(
            "dirctl not found on PATH after ensure_dirctl; check download or install."
        )
    return Path(p).resolve()


# ---------------- Close possibly hanging event loops ----------------
@pytest.fixture(scope="session", autouse=True)
def close_loops_from_policy_factory():
    event_loop_policy = asyncio.get_event_loop_policy()
    if not hasattr(event_loop_policy, "_loop_factory"):
        yield
        return

    loop_factory = event_loop_policy._loop_factory
    loops = []

    def tracking_loop_factory(*args, **kwargs):
        loop = loop_factory(*args, **kwargs)
        loops.append(loop)
        return loop

    event_loop_policy._loop_factory = tracking_loop_factory
    try:
        yield
    finally:
        for loop in loops:
            if not loop.is_closed():
                loop.close()


# ---------------- session infra ----------------
# docker_helpers passes env=os.environ to compose so infra containers use the same env as the test.
files = ["docker/docker-compose.yaml"]
if Path("docker/docker-compose.override.yaml").exists():
    files.append("docker/docker-compose.override.yaml")

_session_docker_torn_down = False


def _teardown_session_docker():
    """Run docker compose down so session containers (zot, dir-api-server, etc) are stopped. Idempotent."""
    global _session_docker_torn_down
    if _session_docker_torn_down:
        return
    _session_docker_torn_down = True
    print("--- Tearing down session Docker (zot, dir-api-server, etc) ---")
    down(files)


atexit.register(_teardown_session_docker)

# Host-side readiness (compose maps zot 5000 to 5555;)
ZOT_REGISTRY_READYZ_URL = "http://127.0.0.1:5555/readyz"

def _wait_http_ready(
    url: str,
    *,
    timeout_s: float = 180.0,
    poll_s: float = 0.5,
    accept_status: tuple[int, ...] = (200,),
) -> None:
    """Poll GET url from the host until status is acceptable or timeout."""
    ok = set(accept_status)
    deadline = time.time() + timeout_s
    last_err: str | None = None
    while time.time() < deadline:
        try:
            resp = httpx.get(url, timeout=2.0)
            if resp.status_code in ok:
                return
            last_err = f"HTTP {resp.status_code}"
        except (httpx.RequestError, httpx.TimeoutException) as e:
            last_err = str(e)
        time.sleep(poll_s)
    raise RuntimeError(
        f"Ready check {url} did not return {accept_status} within {timeout_s}s "
        f"(last: {last_err})"
    )

@pytest.fixture(scope="session", autouse=True)
def orchestrate_session_services():
    """
    Start Directory stack (zot + dir-api-server) for integration tests, analogous
    to lungo's session slim/nats/otel compose setup.
    """
    print("\n--- Setting up session level service integrations ---")
    down(files)
    remove_container_if_exists("docker-dir-api-server-1")
    remove_container_if_exists("docker-zot-1")
    setup_directory_services()
    print("--- Session level service setup complete. Tests can now run ---")
    yield
    _teardown_session_docker()

def setup_directory_services():
    _startup_zot()
    # Same idea as Docker Compose Zot healthcheck: GET /readyz
    _wait_http_ready(ZOT_REGISTRY_READYZ_URL, timeout_s=30.0, poll_s=5.0, accept_status=(200,))

    _startup_dir_api_server()
    # dir-api-server does not expose an HTTP endpoint but rather a gRPC one at 8888.
    # In newer versions of dir-apiserver they do the health check with grpc-health-probe but in apiserver v0.6.0 that was not bundled in the image.
    # For dir-apiserver, this is a fix that will come in a future version (it is not in v1.0.0 but it is fixed in main by https://github.com/agntcy/dir/pull/1017).
    time.sleep(30) # give dir-api-server time to start up; TODO: long-term we should use a more robust wait mechanism.

def _startup_zot():
    up(files, ["zot"])

def _startup_dir_api_server():
    up(files, ["dir-api-server"])



# ---------------- A2A server related fixtures ----------------

def wait_for_server(url: str, timeout: float = 30.0, interval: float = 0.5) -> bool:
    """Wait for a server to become available by polling its agent card endpoint.

    Args:
        url: Base URL of the server
        timeout: Maximum time to wait in seconds
        interval: Time between polling attempts in seconds

    Returns:
        True if server is ready, False if timeout exceeded
    """
    agent_card_url = f"{url}/.well-known/agent.json"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = httpx.get(agent_card_url, timeout=2.0)
            if response.status_code == 200:
                return True
        except (httpx.RequestError, httpx.TimeoutException):
            pass
        time.sleep(interval)

    return False


RECRUITER_SERVER_URL = "http://localhost:8881"


@pytest.fixture
def run_recruiter_a2a_server():
    """Fixture to run the recruiter A2A server in a subprocess.

    Waits for the server to be ready (agent card endpoint returns 200) before
    returning, so tests do not hit ConnectError due to slow startup.
    """

    procs = []

    def _run(wait_timeout: float = 30.0):
        # Use the same Python interpreter as the test
        process = subprocess.Popen(
            [sys.executable, "src/agent_recruiter/server/server.py"],
            env={**os.environ, "ENABLE_HTTP": "true"},
            start_new_session=True,  # Create new process group for clean shutdown
        )
        procs.append(process)

        if not wait_for_server(RECRUITER_SERVER_URL, timeout=wait_timeout):
            process.terminate()
            process.wait(timeout=5)
            raise RuntimeError(
                f"Recruiter A2A server failed to start on {RECRUITER_SERVER_URL} within {wait_timeout}s"
            )
        return process

    yield _run

    # Cleanup: terminate all server processes
    for proc in procs:
        if proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                # Force kill if graceful shutdown fails
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass


@pytest.fixture
def run_sample_a2a_agent():
    """Fixture to run the sample test A2A agent in a subprocess.

    The sample agent runs on port 3210 by default and can be used for
    integration testing with the Rogue evaluator.

    Usage:
        def test_something(run_sample_a2a_agent):
            run_sample_a2a_agent()  # Starts on default port 3210
            # or
            run_sample_a2a_agent(port=3001)  # Custom port

    Returns:
        Tuple of (process, url) where url is the base URL of the agent
    """

    procs = []

    def _run(port: int = 3210, wait_timeout: float = 30.0):
        env = {**os.environ, "PORT": str(port)}
        url = f"http://localhost:{port}"

        process = subprocess.Popen(
            [sys.executable, "-m", "tests.sample_agent.server"],
            env=env,
            start_new_session=True,
        )
        procs.append(process)

        # Wait for server to be ready
        if not wait_for_server(url, timeout=wait_timeout):
            raise RuntimeError(f"Sample agent server failed to start on {url}")

        return process, url

    yield _run

    # Cleanup: terminate all server processes
    for proc in procs:
        if proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass


@pytest.fixture
def sample_agent_url():
    """Returns the default URL for the sample test agent."""
    return "http://localhost:3210"


@pytest.fixture
def sample_agent_card_json():
    """Returns a factory function to create agent card JSON for the test agent.

    Usage:
        def test_something(sample_agent_card_json):
            card_json = sample_agent_card_json()  # Default port 3210
            card_json = sample_agent_card_json(port=3001)  # Custom port
    """
    import json

    def _create(port: int = 3210):
        return json.dumps({
            "name": "TestAgent",
            "description": "A simple test agent for integration testing with basic tools.",
            "url": f"http://localhost:{port}",
            "version": "1.0.0",
            "provider": {
                "organization": "Test Org",
                "url": "http://testorg.example.com"
            },
            "defaultInputModes": ["text/plain"],
            "defaultOutputModes": ["text/plain"],
            "capabilities": {
                "streaming": True,
                "pushNotifications": False
            },
            "skills": []
        })

    return _create


@pytest.fixture
def publish_sample_agent_record():
    """Fixture to publish a sample agent record to the directory and clean up on teardown.

    Uses dirctl to push the record and delete it after the test completes.

    Usage:
        def test_something(publish_sample_agent_record):
            cid = publish_sample_agent_record()  # Uses default record path
            # or
            cid = publish_sample_agent_record(record_path="path/to/record.json")

    Returns:
        The CID of the published record
    """
    published_cids = []

    def _publish(record_path: str = "tests/sample_agent/sample_agent_record.json") -> str:
        """Push a record to the directory and return its CID."""
        # Run dirctl push
        result = subprocess.run(
            ["dirctl", "push", record_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to push record to directory: {result.stderr}\n"
                f"stdout: {result.stdout}"
            )

        # Parse CID from output like "Pushed record with CID: baearei..."
        output = result.stdout + result.stderr
        cid_match = re.search(r"CID:\s*(\S+)", output)
        if not cid_match:
            raise RuntimeError(
                f"Could not parse CID from dirctl output: {output}"
            )

        cid = cid_match.group(1)
        published_cids.append(cid)
        print(f"Published sample agent record with CID: {cid}")
        return cid

    yield _publish

    # Cleanup: delete all published records
    for cid in published_cids:
        try:
            result = subprocess.run(
                ["dirctl", "delete", cid],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                print(f"Deleted sample agent record with CID: {cid}")
            else:
                print(f"Warning: Failed to delete record {cid}: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"Warning: Timeout deleting record {cid}")
        except FileNotFoundError:
            print("Warning: dirctl not found, skipping cleanup")
            break