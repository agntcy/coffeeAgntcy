# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the agentic-workflow list and detail endpoints."""

from __future__ import annotations

from typing import NamedTuple
from unittest.mock import patch

import pytest
from api.agentic_workflows.router import create_agentic_workflows_router
from fastapi import FastAPI
from fastapi.testclient import TestClient
from schema.types import Workflow

_FAKE_WORKFLOWS: dict[str, Workflow] = {
    wf.name: wf
    for wf in [
        Workflow.model_validate(
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
            }
        ),
        Workflow.model_validate(
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
            }
        ),
        Workflow.model_validate(
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
            }
        ),
    ]
}

_ALL_NAMES = {"Pub Sub Coffee", "Group Logistics", "Pub Sub Orders"}

_PATCH_TARGET = "api.agentic_workflows.router.get_workflows"


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    with patch(_PATCH_TARGET, return_value=_FAKE_WORKFLOWS):
        with TestClient(app) as test_client:
            yield test_client


# ---------------------------------------------------------------------------
# GET /agentic-workflows/
# ---------------------------------------------------------------------------


class ListInputs(NamedTuple):
    params: dict[str, str | list[str]]


class ListOutputs(NamedTuple):
    status: int
    expected_names: set[str]


class ListCase(NamedTuple):
    case_id: str
    inputs: ListInputs
    outputs: ListOutputs


_LIST_CASES: tuple[ListCase, ...] = (
    ListCase(
        case_id="no_filters_returns_all",
        inputs=ListInputs(params={}),
        outputs=ListOutputs(status=200, expected_names=_ALL_NAMES),
    ),
    ListCase(
        case_id="filter_single_pattern",
        inputs=ListInputs(params={"patterns": "publish_subscribe"}),
        outputs=ListOutputs(
            status=200,
            expected_names={"Pub Sub Coffee", "Pub Sub Orders"},
        ),
    ),
    ListCase(
        case_id="filter_single_use_case",
        inputs=ListInputs(params={"use_cases": "Order Fulfilment"}),
        outputs=ListOutputs(
            status=200,
            expected_names={"Group Logistics", "Pub Sub Orders"},
        ),
    ),
    ListCase(
        case_id="filter_pattern_and_use_case",
        inputs=ListInputs(
            params={
                "patterns": "publish_subscribe",
                "use_cases": "Order Fulfilment",
            }
        ),
        outputs=ListOutputs(status=200, expected_names={"Pub Sub Orders"}),
    ),
    ListCase(
        case_id="filter_no_match_returns_empty",
        inputs=ListInputs(params={"patterns": "nonexistent"}),
        outputs=ListOutputs(status=200, expected_names=set()),
    ),
    ListCase(
        case_id="filter_multiple_patterns",
        inputs=ListInputs(
            params={"patterns": ["publish_subscribe", "group_communication"]}
        ),
        outputs=ListOutputs(status=200, expected_names=_ALL_NAMES),
    ),
)


@pytest.mark.parametrize(
    "case", [pytest.param(c, id=c.case_id) for c in _LIST_CASES]
)
def test_list_agentic_workflows(case: ListCase, client: TestClient) -> None:
    resp = client.get("/agentic-workflows/", params=case.inputs.params)
    assert resp.status_code == case.outputs.status

    data = resp.json()
    assert set(data.keys()) == case.outputs.expected_names

    for name, summary in data.items():
        assert summary["name"] == name
        assert set(summary.keys()) == {"name", "pattern", "use_case"}


# ---------------------------------------------------------------------------
# GET /agentic-workflows/{workflow_name}/
# ---------------------------------------------------------------------------


class DetailInputs(NamedTuple):
    workflow_name: str
    topology_only: bool | None


class DetailOutputs(NamedTuple):
    status: int
    expected_name: str | None
    expected_pattern: str | None
    expected_use_case: str | None
    instances_empty: bool | None


class DetailCase(NamedTuple):
    case_id: str
    inputs: DetailInputs
    outputs: DetailOutputs


_DETAIL_CASES: tuple[DetailCase, ...] = (
    DetailCase(
        case_id="existing_workflow",
        inputs=DetailInputs(
            workflow_name="Pub Sub Coffee", topology_only=None
        ),
        outputs=DetailOutputs(
            status=200,
            expected_name="Pub Sub Coffee",
            expected_pattern="publish_subscribe",
            expected_use_case="Coffee Buying",
            instances_empty=True,
        ),
    ),
    DetailCase(
        case_id="unknown_workflow_404",
        inputs=DetailInputs(
            workflow_name="does-not-exist", topology_only=None
        ),
        outputs=DetailOutputs(
            status=404,
            expected_name=None,
            expected_pattern=None,
            expected_use_case=None,
            instances_empty=None,
        ),
    ),
    DetailCase(
        case_id="topology_only_true",
        inputs=DetailInputs(
            workflow_name="Pub Sub Coffee", topology_only=True
        ),
        outputs=DetailOutputs(
            status=200,
            expected_name="Pub Sub Coffee",
            expected_pattern="publish_subscribe",
            expected_use_case="Coffee Buying",
            instances_empty=True,
        ),
    ),
    DetailCase(
        case_id="topology_only_false_same_as_default",
        inputs=DetailInputs(
            workflow_name="Pub Sub Coffee", topology_only=False
        ),
        outputs=DetailOutputs(
            status=200,
            expected_name="Pub Sub Coffee",
            expected_pattern="publish_subscribe",
            expected_use_case="Coffee Buying",
            instances_empty=True,
        ),
    ),
)


@pytest.mark.parametrize(
    "case", [pytest.param(c, id=c.case_id) for c in _DETAIL_CASES]
)
def test_get_agentic_workflow(case: DetailCase, client: TestClient) -> None:
    params = {}
    if case.inputs.topology_only is not None:
        params["topology_only"] = case.inputs.topology_only

    resp = client.get(
        f"/agentic-workflows/{case.inputs.workflow_name}/", params=params
    )
    assert resp.status_code == case.outputs.status

    if case.outputs.status != 200:
        return

    data = resp.json()
    assert data["name"] == case.outputs.expected_name
    assert data["pattern"] == case.outputs.expected_pattern
    assert data["use_case"] == case.outputs.expected_use_case
    assert "starting_topology" in data
    assert isinstance(data["starting_topology"]["nodes"], list)
    assert isinstance(data["starting_topology"]["edges"], list)

    if case.outputs.instances_empty:
        assert data["instances"] == {}
