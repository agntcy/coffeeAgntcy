# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the agentic-workflow list and detail endpoints."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from api.agentic_workflows.router import create_agentic_workflows_router
from fastapi import FastAPI
from fastapi.testclient import TestClient

_FAKE_WORKFLOWS: list[dict[str, Any]] = [
    {
        "pattern": "publish_subscribe",
        "use_case": "Coffee Buying",
        "name": "Pub Sub Coffee",
        "starting_topology": {
            "nodes": [
                {
                    "id": "node://00000000-0000-4000-a000-000000000001",
                    "operation": "read",
                    "type": "customNode",
                    "label": "Agent A",
                    "size": {"width": 1.0, "height": 1.0},
                    "layer_index": 0,
                },
            ],
            "edges": [],
        },
        "instances": {},
    },
    {
        "pattern": "group_communication",
        "use_case": "Order Fulfilment",
        "name": "Group Logistics",
        "starting_topology": {
            "nodes": [
                {
                    "id": "node://00000000-0000-4000-a000-000000000002",
                    "operation": "read",
                    "type": "customNode",
                    "label": "Agent B",
                    "size": {"width": 1.0, "height": 1.0},
                    "layer_index": 0,
                },
            ],
            "edges": [],
        },
        "instances": {},
    },
    {
        "pattern": "publish_subscribe",
        "use_case": "Order Fulfilment",
        "name": "Pub Sub Orders",
        "starting_topology": {
            "nodes": [
                {
                    "id": "node://00000000-0000-4000-a000-000000000003",
                    "operation": "read",
                    "type": "customNode",
                    "label": "Agent C",
                    "size": {"width": 1.0, "height": 1.0},
                    "layer_index": 0,
                },
            ],
            "edges": [],
        },
        "instances": {},
    },
]

_PATCH_TARGET = "api.agentic_workflows.router.get_starting_workflows"


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    with patch(_PATCH_TARGET, return_value=_FAKE_WORKFLOWS):
        yield TestClient(app)


# ---------------------------------------------------------------------------
# GET /agentic-workflows/
# ---------------------------------------------------------------------------


class TestListAgenticWorkflows:
    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get("/agentic-workflows/")
        assert resp.status_code == 200

    def test_returns_all_workflows_when_no_filters(self, client: TestClient) -> None:
        data = client.get("/agentic-workflows/").json()
        assert set(data.keys()) == {
            "Pub Sub Coffee",
            "Group Logistics",
            "Pub Sub Orders",
        }

    def test_each_entry_has_required_fields(self, client: TestClient) -> None:
        data = client.get("/agentic-workflows/").json()
        for name, summary in data.items():
            assert summary["name"] == name
            assert "pattern" in summary
            assert "use_case" in summary

    def test_no_extra_fields_on_summary(self, client: TestClient) -> None:
        data = client.get("/agentic-workflows/").json()
        for summary in data.values():
            assert set(summary.keys()) == {"name", "pattern", "use_case"}

    def test_filter_by_single_pattern(self, client: TestClient) -> None:
        resp = client.get(
            "/agentic-workflows/", params={"patterns": "publish_subscribe"}
        )
        data = resp.json()
        assert set(data.keys()) == {"Pub Sub Coffee", "Pub Sub Orders"}

    def test_filter_by_single_use_case(self, client: TestClient) -> None:
        resp = client.get(
            "/agentic-workflows/", params={"use_cases": "Order Fulfilment"}
        )
        data = resp.json()
        assert set(data.keys()) == {"Group Logistics", "Pub Sub Orders"}

    def test_filter_by_pattern_and_use_case(self, client: TestClient) -> None:
        resp = client.get(
            "/agentic-workflows/",
            params={
                "patterns": "publish_subscribe",
                "use_cases": "Order Fulfilment",
            },
        )
        data = resp.json()
        assert set(data.keys()) == {"Pub Sub Orders"}

    def test_filter_no_match_returns_empty_map(self, client: TestClient) -> None:
        resp = client.get(
            "/agentic-workflows/", params={"patterns": "nonexistent"}
        )
        assert resp.status_code == 200
        assert resp.json() == {}

    def test_filter_by_multiple_patterns(self, client: TestClient) -> None:
        resp = client.get(
            "/agentic-workflows/",
            params={"patterns": ["publish_subscribe", "group_communication"]},
        )
        data = resp.json()
        assert set(data.keys()) == {
            "Pub Sub Coffee",
            "Group Logistics",
            "Pub Sub Orders",
        }


# ---------------------------------------------------------------------------
# GET /agentic-workflows/{workflow_name}/
# ---------------------------------------------------------------------------


class TestGetAgenticWorkflow:
    def test_returns_200_for_existing_workflow(self, client: TestClient) -> None:
        resp = client.get("/agentic-workflows/Pub Sub Coffee/")
        assert resp.status_code == 200

    def test_returns_404_for_unknown_workflow(self, client: TestClient) -> None:
        resp = client.get("/agentic-workflows/does-not-exist/")
        assert resp.status_code == 404

    def test_response_contains_workflow_fields(self, client: TestClient) -> None:
        data = client.get("/agentic-workflows/Pub Sub Coffee/").json()
        assert data["name"] == "Pub Sub Coffee"
        assert data["pattern"] == "publish_subscribe"
        assert data["use_case"] == "Coffee Buying"
        assert "starting_topology" in data
        assert "instances" in data

    def test_starting_topology_has_nodes_and_edges(self, client: TestClient) -> None:
        topo = client.get("/agentic-workflows/Pub Sub Coffee/").json()[
            "starting_topology"
        ]
        assert "nodes" in topo
        assert "edges" in topo
        assert isinstance(topo["nodes"], list)
        assert isinstance(topo["edges"], list)

    def test_topology_only_returns_empty_instances(self, client: TestClient) -> None:
        data = client.get(
            "/agentic-workflows/Pub Sub Coffee/",
            params={"topology_only": True},
        ).json()
        assert data["instances"] == {}
        assert "starting_topology" in data

    def test_topology_only_preserves_identity_fields(
        self, client: TestClient
    ) -> None:
        data = client.get(
            "/agentic-workflows/Pub Sub Coffee/",
            params={"topology_only": True},
        ).json()
        assert data["name"] == "Pub Sub Coffee"
        assert data["pattern"] == "publish_subscribe"
        assert data["use_case"] == "Coffee Buying"

    def test_default_topology_only_is_false(self, client: TestClient) -> None:
        full = client.get("/agentic-workflows/Pub Sub Coffee/").json()
        topo = client.get(
            "/agentic-workflows/Pub Sub Coffee/",
            params={"topology_only": False},
        ).json()
        assert full == topo
