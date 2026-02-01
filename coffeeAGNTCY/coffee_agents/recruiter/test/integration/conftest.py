# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys
import os
import signal
import time
import re
import pytest
import httpx
from dotenv import load_dotenv

load_dotenv()


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


@pytest.fixture
def run_recruiter_a2a_server():
    """Fixture to run the recruiter A2A server in a subprocess."""

    procs = []

    def _run():
        # Use the same Python interpreter as the test
        process = subprocess.Popen(
            [sys.executable, "src/agent_recruiter/server/server.py"],
            env={**os.environ, "ENABLE_HTTP": "true"},
            start_new_session=True,  # Create new process group for clean shutdown
        )
        procs.append(process)

        time.sleep(2)  # Wait for server to start
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

    The sample agent runs on port 3000 by default and can be used for
    integration testing with the Rogue evaluator.

    Usage:
        def test_something(run_sample_a2a_agent):
            run_sample_a2a_agent()  # Starts on default port 3000
            # or
            run_sample_a2a_agent(port=3001)  # Custom port

    Returns:
        Tuple of (process, url) where url is the base URL of the agent
    """

    procs = []

    def _run(port: int = 3000, wait_timeout: float = 30.0):
        env = {**os.environ, "PORT": str(port)}
        url = f"http://localhost:{port}"

        process = subprocess.Popen(
            [sys.executable, "-m", "test.sample_agent.server"],
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
    return "http://localhost:3000"


@pytest.fixture
def sample_agent_card_json():
    """Returns a factory function to create agent card JSON for the test agent.

    Usage:
        def test_something(sample_agent_card_json):
            card_json = sample_agent_card_json()  # Default port 3000
            card_json = sample_agent_card_json(port=3001)  # Custom port
    """
    import json

    def _create(port: int = 3000):
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

    def _publish(record_path: str = "test/sample_agent/sample_agent_record.json") -> str:
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