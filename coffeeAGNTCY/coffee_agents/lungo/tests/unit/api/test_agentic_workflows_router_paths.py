# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Regression: instance-scoped routes use a bare UUID path segment (issue #525 / Option A)."""

from __future__ import annotations

from typing import NamedTuple
from unittest.mock import patch
from uuid import UUID

import pytest
from api.agentic_workflows.instance_lifecycle import build_instantiate_seed_event
from api.agentic_workflows.router import (
    WORKFLOW_INSTANCE_STORE_ATTR,
    create_agentic_workflows_router,
)
from common.workflow_instance_store import WorkflowInstanceStateStore
from fastapi import FastAPI
from fastapi.testclient import TestClient
from schema.types import Workflow, instance_id_from_uuid

_INSTANCE_UUID = UUID("550e8400-e29b-41d4-a716-446655440000")
_BARE_UUID_PATH = "/agentic-workflows/W/instances/550e8400-e29b-41d4-a716-446655440000"

_WF_W = Workflow.model_validate(
    {
        "pattern": "p",
        "use_case": "u",
        "scenario": "s",
        "name": "W",
        "starting_topology": {
            "nodes": [
                {
                    "id": "node://00000000-0000-4000-a000-000000000001",
                    "operation": "read",
                    "type": "customNode",
                    "label": "n",
                    "size": {"width": 1.0, "height": 1.0},
                    "layer_index": 0,
                },
            ],
            "edges": [],
        },
        "instances": {},
    }
)

_PATCH = "api.agentic_workflows.router.get_workflows"


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI()
    store = WorkflowInstanceStateStore()
    setattr(app.state, WORKFLOW_INSTANCE_STORE_ATTR, store)
    app.include_router(create_agentic_workflows_router())
    iuri = instance_id_from_uuid(_INSTANCE_UUID).root
    seed = build_instantiate_seed_event(_WF_W, "W", iuri)
    store.submit_event_sync(seed)
    store.wait_merge_idle()
    try:
        with patch(_PATCH, return_value={"W": _WF_W}):
            with TestClient(app) as c:
                yield c
    finally:
        store.close()


# ---------------------------------------------------------------------------
# HTTP routing: bare UUID must match; legacy instance:// path must not
# ---------------------------------------------------------------------------


class RouteCase(NamedTuple):
    """``case_id`` is the pytest parametrization id."""

    case_id: str
    method: str
    path: str
    json_body: dict | None
    expect_404: bool


_ROUTE_CASES: tuple[RouteCase, ...] = (
    RouteCase(
        case_id="post_events_bare_uuid",
        method="POST",
        path="/agentic-workflows/Some%20Workflow/instances/550e8400-e29b-41d4-a716-446655440000/events/",
        json_body={},
        expect_404=False,
    ),
    RouteCase(
        case_id="get_instance_state_bare_uuid",
        method="GET",
        path=f"{_BARE_UUID_PATH}/",
        json_body=None,
        expect_404=False,
    ),
    RouteCase(
        case_id="events_stream_route_registered_bare_uuid",
        method="HEAD",
        path=f"{_BARE_UUID_PATH}/events/stream",
        json_body=None,
        expect_404=False,
    ),
    RouteCase(
        case_id="post_events_legacy_instance_uri_in_path",
        method="POST",
        path=(
            "/agentic-workflows/W/instances/instance://"
            "550e8400-e29b-41d4-a716-446655440000/events/"
        ),
        json_body={},
        expect_404=True,
    ),
)


@pytest.mark.parametrize(
    "case", [pytest.param(c, id=c.case_id) for c in _ROUTE_CASES]
)
def test_instance_scoped_routes(case: RouteCase, client: TestClient) -> None:
    if case.method == "GET":
        resp = client.get(case.path)
    elif case.method == "HEAD":
        resp = client.head(case.path)
    elif case.method == "POST":
        resp = client.post(case.path, json=case.json_body or {})
    else:
        raise AssertionError(f"unsupported method: {case.method!r}")

    if case.expect_404:
        assert resp.status_code == 404
    else:
        assert resp.status_code != 404


# ---------------------------------------------------------------------------
# Canonical InstanceId from path UUID
# ---------------------------------------------------------------------------


class CanonicalIdCase(NamedTuple):
    case_id: str
    workflow_instance_uuid: UUID
    expected_instance_uri: str


_CANONICAL_ID_CASES: tuple[CanonicalIdCase, ...] = (
    CanonicalIdCase(
        case_id="hyphenated_uuid",
        workflow_instance_uuid=_INSTANCE_UUID,
        expected_instance_uri="instance://550e8400-e29b-41d4-a716-446655440000",
    ),
)


@pytest.mark.parametrize(
    "case", [pytest.param(c, id=c.case_id) for c in _CANONICAL_ID_CASES]
)
def test_instance_id_from_uuid(case: CanonicalIdCase) -> None:
    got = instance_id_from_uuid(case.workflow_instance_uuid)
    assert got.root == case.expected_instance_uri
