# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
import time
from typing import Optional, Tuple
import json
from typing import List
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2] 

def _compose_cmd(files: List[str]) -> List[str]:
    """
    Build a docker compose command ensuring:
      - All compose file paths are absolute (rooted at PROJECT_DIR) so invocation
        location does not matter.
    """
    cmd = ["docker", "compose"]
    for f in files:
        if f.strip():
            compose_file = (PROJECT_DIR / f.strip()).resolve()
            cmd += ["-f", str(compose_file)]
    return cmd

def _run(cmd: List[str]):
    """
    Execute a docker compose command from PROJECT_DIR to make calls location-agnostic.
    """
    print(">", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True, cwd=PROJECT_DIR)
    except subprocess.CalledProcessError:
        # Show resolved config (catches missing env like LLM_PROVIDER)
        subprocess.run(
            ["docker", "compose", "-f", str((PROJECT_DIR / "docker-compose.yaml").resolve()), "config"],
            check=False,
            cwd=PROJECT_DIR,
        )
        # Show recent logs for the target service(s) if any
        try:
            services = [a for a in cmd if not a.startswith("-")]
            svc = services[-1] if services and services[-1] not in ("up", "down", "build") else None
            if svc:
                subprocess.run(
                    ["docker", "compose", "-f", str((PROJECT_DIR / "docker-compose.yaml").resolve()), "logs", "--no-color", "--tail=200", svc],
                    check=False,
                    cwd=PROJECT_DIR,
                )
        except Exception:
            pass
        raise

def up(files: List[str], services: List[str]):
    cmd = _compose_cmd(files) + ["up", "-d", "--build"] + services
    _run(cmd)
    for svc in services:
        wait_for_service(files, svc)

def down(files: List[str]):
    # 'down' ignores service list; it tears down the whole project
    cmd = _compose_cmd(files) + ["down", "-v"]
    _run(cmd)

def _container_id(files: List[str], service: str) -> str:
    cmd = _compose_cmd(files) + ["ps", "-q", service]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_DIR)
    if res.returncode != 0:
        raise RuntimeError(f"`compose ps -q {service}` failed: {res.stderr.strip()}")
    cid = res.stdout.strip()
    if not cid:
        # maybe service not known, or different project dir/file
        raise RuntimeError(f"No container id found for service '{service}'. Check compose file/path and project.")
    return cid

def _inspect_state_health(container_id: str) -> Tuple[str, Optional[str]]:
    """
    Return (state, health) where state in {"created","running","exited","restarting","removing","dead"}
    and health in {"healthy","unhealthy","starting", None}
    """
    res = subprocess.run(
        ["docker", "inspect", container_id],
        capture_output=True, text=True
    )
    if res.returncode != 0:
        raise RuntimeError(f"`docker inspect` failed for {container_id}: {res.stderr.strip()}")
    data = json.loads(res.stdout)[0]
    state = data.get("State", {})
    status = state.get("Status")  # docker's running/exited/etc
    health = None
    if "Health" in state and state["Health"]:
        health = state["Health"].get("Status")  # healthy/unhealthy/starting
    return status, health

def _compose_logs(files: List[str], service: str, tail: int = 200):
    try:
        _run(_compose_cmd(files) + ["logs", "--no-color", f"--tail={tail}", service])
    except Exception:
        pass

def wait_for_service(files: List[str], service: str, timeout: float = 45.0, poll: float = 0.5):
    """
    Wait until the service container is running, and if it has a healthcheck, until it is healthy.
    On timeout, print logs and raise.
    """
    deadline = time.time() + timeout
    cid = _container_id(files, service)  # ensures same compose context
    last_state, last_health = None, None
    while time.time() < deadline:
        state, health = _inspect_state_health(cid)
        if health:  # healthcheck present
            if health == "healthy":
                print(f"Service {service} is healthy (container {cid[:12]}).")
                return
        else:
            if state == "running":
                print(f"Service {service} is running (container {cid[:12]}).")
                return

        if (state, health) != (last_state, last_health):
            print(f"Waiting for {service}: state={state}, health={health}")
            last_state, last_health = (state, health)
        time.sleep(poll)

    print(f"Timed out waiting for {service}. Dumping logs:")
    _compose_logs(files, service)
    raise RuntimeError(f"Service {service} did not become ready (state={last_state}, health={last_health})")