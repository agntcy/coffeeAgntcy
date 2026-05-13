# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from urllib.parse import quote

import pytest
from api.agentic_workflows.router import create_agentic_workflows_router
from api.agentic_workflows.workflow_documentation import (
    load_parsed_workflow_documentation,
    workflow_name_to_documentation_slug,
)
from api.agentic_workflows.workflows import set_starting_workflows
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("name", "expected_slug"),
    [
        (
            "Publish Subscribe Coffee Farm Network",
            "publish_subscribe_coffee_farm_network",
        ),
        ("On-demand Discovery", "on-demand_discovery"),
        ("Event Ledger (Episodic Memory)", "event_ledger_episodic_memory"),
        ("Coordinator + Worker Agents", "coordinator_+_worker_agents"),
        ("Resilience & Re-Routing", "resilience_&_re-routing"),
        ("Sense–Decide–Act Loop", "sense_decide_act_loop"),
    ],
)
def test_workflow_name_to_documentation_slug(name: str, expected_slug: str) -> None:
    assert workflow_name_to_documentation_slug(name) == expected_slug


def test_load_parsed_real_file_has_pattern_section() -> None:
    parsed = load_parsed_workflow_documentation("publish_subscribe_coffee_farm_network")
    assert parsed is not None
    headings = [h for _, h, _ in parsed.sections]
    assert "Pattern" in headings


@pytest.fixture()
def doc_client() -> TestClient:
    set_starting_workflows()
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    return TestClient(app)


def test_get_workflow_documentation_200(doc_client: TestClient) -> None:
    name = "Publish Subscribe Coffee Farm Network"
    r = doc_client.get(
        f"/agentic-workflows/{quote(name, safe='')}/documentation/",
    )
    assert r.status_code == 200
    data = r.json()
    assert data["workflow_name"] == name
    assert data["slug"] == "publish_subscribe_coffee_farm_network"
    assert any(s["heading"] == "Pattern" for s in data["sections"])
    assert len(data["full_markdown"]) > 0


def test_get_workflow_documentation_unknown_workflow(doc_client: TestClient) -> None:
    r = doc_client.get(
        "/agentic-workflows/NoSuchWorkflowName/documentation/",
    )
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()
