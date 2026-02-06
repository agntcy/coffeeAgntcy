# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared fixtures for recruiter supervisor unit tests."""

import importlib
import sys

import pytest
from fastapi.testclient import TestClient


def _purge_modules(prefixes):
    to_delete = [
        m
        for m in list(sys.modules)
        if any(m == p or m.startswith(p + ".") for p in prefixes)
    ]
    for m in to_delete:
        sys.modules.pop(m, None)


@pytest.fixture()
def recruiter_client(monkeypatch):
    """Create a TestClient for the recruiter supervisor FastAPI app.

    Sets a dummy LLM_MODEL so agent.py can initialise without a real provider.
    Purges cached modules so monkeypatched env vars take effect.
    """
    monkeypatch.setenv("LLM_MODEL", "openai/gpt-4o-mini")
    monkeypatch.setenv("RECRUITER_AGENT_URL", "http://localhost:8881")

    _purge_modules([
        "agents.supervisors.recruiter",
        "config.config",
    ])

    import agents.supervisors.recruiter.main as recruiter_main

    importlib.reload(recruiter_main)

    with TestClient(recruiter_main.app) as client:
        yield client


# -- sample data used across tests ------------------------------------------

SAMPLE_AGENT_RECORD = {
    "name": "Accounting Agent",
    "description": "Handles accounting and invoicing tasks",
    "url": "http://localhost:9000",
    "version": "1.0.0",
}

SAMPLE_RECRUITED_AGENTS = {
    "cid_abc123": {
        "name": "Accounting Agent",
        "description": "Handles accounting",
        "url": "http://localhost:9000",
    },
    "cid_def456": {
        "name": "Shipping Agent",
        "description": "Handles shipping logistics",
        "url": "http://localhost:9001",
    },
}
