# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""HTTP tests for workflow instance lifecycle (POST instantiate, GET list, GET state)."""

from __future__ import annotations

from typing import NamedTuple
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from api.agentic_workflows.instance_lifecycle import (
    build_instantiate_seed_event,
    instances_map_for_workflow,
    workflow_instance_from_projection,
)
from api.agentic_workflows.router import (
    INSTANTIATE_MERGE_WAIT_TIMEOUT_DETAIL,
    WORKFLOW_INSTANCE_STORE_ATTR,
    create_agentic_workflows_router,
)
from common.workflow_instance_store import WorkflowInstanceStateStore
from fastapi import FastAPI
from fastapi.testclient import TestClient
from schema.types import Data, Event, Workflow, instance_id_from_uuid

_PATCH_GET_WORKFLOWS = "api.agentic_workflows.router.get_workflows"

_MINIMAL_WORKFLOWS: dict[str, Workflow] = {
    "InstTestWf": Workflow.model_validate(
        {
            "name": "InstTestWf",
            "pattern": "test_pattern",
            "use_case": "test_uc",
            "scenario": "test_scenario",
            "starting_topology": {
                "nodes": [
                    {
                        "id": "node://00000000-0000-4000-a000-0000000000aa",
                        "operation": "read",
                        "type": "customNode",
                        "label": "OnlyNode",
                        "size": {"width": 1.0, "height": 1.0},
                        "layer_index": 0,
                    },
                ],
                "edges": [],
            },
            "instances": {},
        }
    ),
}


@pytest.fixture()
def app_with_store() -> FastAPI:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    store = WorkflowInstanceStateStore()
    setattr(app.state, WORKFLOW_INSTANCE_STORE_ATTR, store)
    app.include_router(create_agentic_workflows_router())
    try:
        yield app
    finally:
        store.close()


@pytest.fixture()
def client(
    app_with_store: FastAPI,
    workflow_api_headers: dict[str, str],
) -> TestClient:
    with patch(_PATCH_GET_WORKFLOWS, return_value=_MINIMAL_WORKFLOWS):
        with TestClient(app_with_store, headers=workflow_api_headers) as c:
            yield c


def test_list_instances_unknown_workflow_returns_404(client: TestClient) -> None:
    r = client.get("/agentic-workflows/NoSuchWorkflow/instances/")
    assert r.status_code == 404


def test_list_instances_known_workflow_empty_store_returns_200_empty_map(
    client: TestClient,
) -> None:
    r = client.get("/agentic-workflows/InstTestWf/instances/")
    assert r.status_code == 200
    assert r.json() == {}


def test_post_instantiate_unknown_workflow_returns_404(client: TestClient) -> None:
    r = client.post("/agentic-workflows/MissingWf/")
    assert r.status_code == 404


def test_get_instance_unknown_workflow_returns_404(client: TestClient) -> None:
    uid = UUID("550e8400-e29b-41d4-a716-446655440099")
    r = client.get(f"/agentic-workflows/NoSuch/instances/{uid}/")
    assert r.status_code == 404


def test_get_instance_unknown_instance_returns_404(client: TestClient) -> None:
    uid = UUID("550e8400-e29b-41d4-a716-446655440088")
    r = client.get(f"/agentic-workflows/InstTestWf/instances/{uid}/")
    assert r.status_code == 404


def test_instantiate_list_get_round_trip_and_topology(client: TestClient) -> None:
    wf_name = "InstTestWf"
    post = client.post(f"/agentic-workflows/{wf_name}/")
    assert post.status_code == 200, post.text
    body = post.json()
    wid = body["workflow_instance_id"]
    assert wid.startswith("instance://")
    path_uuid = UUID(wid.removeprefix("instance://"))

    listed = client.get(f"/agentic-workflows/{wf_name}/instances/")
    assert listed.status_code == 200
    m = listed.json()
    assert wid in m
    assert m[wid]["id"] == wid

    got = client.get(f"/agentic-workflows/{wf_name}/instances/{path_uuid}/")
    assert got.status_code == 200
    full = got.json()
    assert full["id"] == wid
    topo = full["topology"]
    assert "nodes" in topo
    assert len(topo["nodes"]) == 1
    assert topo["nodes"][0]["id"] == "node://00000000-0000-4000-a000-0000000000aa"

    topo_only = client.get(
        f"/agentic-workflows/{wf_name}/instances/{path_uuid}/",
        params={"topology_only": "true"},
    )
    assert topo_only.status_code == 200
    slim = topo_only.json()
    assert set(slim.keys()) == {"id", "topology"}
    assert slim["topology"] == topo


def test_build_instantiate_seed_event_validates_as_event_and_merges() -> None:
    wf = _MINIMAL_WORKFLOWS["InstTestWf"]
    iuri = instance_id_from_uuid(uuid4()).root
    raw = build_instantiate_seed_event(wf, "InstTestWf", iuri)
    ev = Event.model_validate(raw)
    assert ev.metadata.id.root.startswith("event://")
    assert ev.metadata.correlation.id.root.startswith("correlation://")
    assert ev.data.workflows["InstTestWf"].instances[iuri].id.root == iuri

    store = WorkflowInstanceStateStore()
    try:
        store.submit_event_sync(raw)
        store.wait_merge_idle()
        proj = store.get_instance_projection("InstTestWf", iuri)
        assert proj is not None
        inst = workflow_instance_from_projection(proj, iuri, topology_only=False)
        assert inst.id.root == iuri
        assert inst.topology.nodes is not None
        assert len(inst.topology.nodes) == 1
        only = workflow_instance_from_projection(proj, iuri, topology_only=True)
        dumped = only.model_dump(mode="json", exclude_none=True)
        assert set(dumped.keys()) == {"id", "topology"}
    finally:
        store.close()


def test_instances_map_for_workflow_missing_block() -> None:
    data = Data(workflows={})
    assert instances_map_for_workflow(data, "InstTestWf") == {}


def test_instantiate_without_store_returns_503(
    workflow_api_headers: dict[str, str],
) -> None:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    with patch(_PATCH_GET_WORKFLOWS, return_value=_MINIMAL_WORKFLOWS):
        with TestClient(app, headers=workflow_api_headers) as client:
            r = client.post("/agentic-workflows/InstTestWf/")
    assert r.status_code == 503
    assert "not configured" in r.json()["detail"].lower()


def test_list_instances_without_store_returns_503(
    workflow_api_headers: dict[str, str],
) -> None:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    with patch(_PATCH_GET_WORKFLOWS, return_value=_MINIMAL_WORKFLOWS):
        with TestClient(app, headers=workflow_api_headers) as client:
            r = client.get("/agentic-workflows/InstTestWf/instances/")
    assert r.status_code == 503
    assert "not configured" in r.json()["detail"].lower()


def test_get_instance_without_store_returns_503(
    workflow_api_headers: dict[str, str],
) -> None:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    uid = UUID("550e8400-e29b-41d4-a716-4466554400dd")
    with patch(_PATCH_GET_WORKFLOWS, return_value=_MINIMAL_WORKFLOWS):
        with TestClient(app, headers=workflow_api_headers) as client:
            r = client.get(f"/agentic-workflows/InstTestWf/instances/{uid}/")
    assert r.status_code == 503
    assert "not configured" in r.json()["detail"].lower()


def test_build_instantiate_seed_event_rejects_workflow_name_mismatch() -> None:
    wf = _MINIMAL_WORKFLOWS["InstTestWf"]
    iuri = instance_id_from_uuid(uuid4()).root
    with pytest.raises(ValueError, match="must equal Workflow.name"):
        build_instantiate_seed_event(wf, "WrongCatalogKey", iuri)


def test_instantiate_merge_wait_timeout_returns_504(
    client: TestClient,
    app_with_store: FastAPI,
) -> None:
    store = getattr(app_with_store.state, WORKFLOW_INSTANCE_STORE_ATTR)
    with patch.object(
        store,
        "wait_merge_idle",
        side_effect=TimeoutError("Timed out waiting for merge queue to drain"),
    ):
        r = client.post("/agentic-workflows/InstTestWf/")
    assert r.status_code == 504
    assert r.json()["detail"] == INSTANTIATE_MERGE_WAIT_TIMEOUT_DETAIL


def test_instantiate_merge_wait_timeout_event_still_merges(
    client: TestClient,
    app_with_store: FastAPI,
) -> None:
    wf_name = "InstTestWf"
    pre = client.get(f"/agentic-workflows/{wf_name}/instances/")
    assert pre.status_code == 200
    baseline = len(pre.json())

    store = getattr(app_with_store.state, WORKFLOW_INSTANCE_STORE_ATTR)
    with patch.object(
        store,
        "wait_merge_idle",
        side_effect=TimeoutError("Timed out waiting for merge queue to drain"),
    ):
        r = client.post(f"/agentic-workflows/{wf_name}/")
    assert r.status_code == 504

    store.wait_merge_idle()
    post = client.get(f"/agentic-workflows/{wf_name}/instances/")
    assert post.status_code == 200
    assert len(post.json()) == baseline + 1


def test_multiple_instantiations_list_two_instances(client: TestClient) -> None:
    wf_name = "InstTestWf"
    r1 = client.post(f"/agentic-workflows/{wf_name}/")
    r2 = client.post(f"/agentic-workflows/{wf_name}/")
    assert r1.status_code == 200
    assert r2.status_code == 200
    wid1 = r1.json()["workflow_instance_id"]
    wid2 = r2.json()["workflow_instance_id"]
    assert wid1 != wid2

    listed = client.get(f"/agentic-workflows/{wf_name}/instances/")
    assert listed.status_code == 200
    m = listed.json()
    assert len(m) == 2
    assert wid1 in m and wid2 in m

    u1 = UUID(wid1.removeprefix("instance://"))
    u2 = UUID(wid2.removeprefix("instance://"))
    g1 = client.get(f"/agentic-workflows/{wf_name}/instances/{u1}/")
    g2 = client.get(f"/agentic-workflows/{wf_name}/instances/{u2}/")
    assert g1.status_code == 200
    assert g2.status_code == 200
    assert g1.json()["id"] == wid1
    assert g2.json()["id"] == wid2


class DeleteHttpCase(NamedTuple):
    case_id: str
    workflow_name: str
    path_uuid: UUID
    expected_status: int


_DELETE_HTTP_CASES: tuple[DeleteHttpCase, ...] = (
    DeleteHttpCase(
        case_id="unknown_workflow",
        workflow_name="NoSuch",
        path_uuid=UUID("550e8400-e29b-41d4-a716-446655440011"),
        expected_status=404,
    ),
    DeleteHttpCase(
        case_id="unknown_instance_on_known_workflow",
        workflow_name="InstTestWf",
        path_uuid=UUID("550e8400-e29b-41d4-a716-446655440012"),
        expected_status=204,
    ),
)


@pytest.mark.parametrize(
    "case", [pytest.param(c, id=c.case_id) for c in _DELETE_HTTP_CASES]
)
def test_delete_workflow_instance_http_status(
    client: TestClient,
    case: DeleteHttpCase,
) -> None:
    r = client.delete(
        f"/agentic-workflows/{case.workflow_name}/instances/{case.path_uuid}/",
    )
    assert r.status_code == case.expected_status


class DeleteIdempotentCase(NamedTuple):
    case_id: str
    delete_index: int
    expected_status: int


_DELETE_IDEMPOTENT_CASES: tuple[DeleteIdempotentCase, ...] = (
    DeleteIdempotentCase(
        case_id="first_delete_existing_instance",
        delete_index=0,
        expected_status=202,
    ),
    DeleteIdempotentCase(
        case_id="second_delete_already_removed",
        delete_index=1,
        expected_status=204,
    ),
)


@pytest.mark.parametrize(
    "case", [pytest.param(c, id=c.case_id) for c in _DELETE_IDEMPOTENT_CASES]
)
def test_delete_workflow_instance_idempotent_status(
    client: TestClient,
    case: DeleteIdempotentCase,
) -> None:
    wf_name = "InstTestWf"
    post = client.post(f"/agentic-workflows/{wf_name}/")
    assert post.status_code == 200
    wid = post.json()["workflow_instance_id"]
    path_uuid = UUID(wid.removeprefix("instance://"))

    for index in range(case.delete_index + 1):
        r = client.delete(f"/agentic-workflows/{wf_name}/instances/{path_uuid}/")
        if index == case.delete_index:
            assert r.status_code == case.expected_status

    if case.delete_index == 1:
        listed = client.get(f"/agentic-workflows/{wf_name}/instances/")
        assert listed.status_code == 200
        assert wid not in listed.json()


def test_instantiate_delete_then_post_event_returns_404(
    client: TestClient,
) -> None:
    wf_name = "InstTestWf"
    post = client.post(f"/agentic-workflows/{wf_name}/")
    assert post.status_code == 200
    wid = post.json()["workflow_instance_id"]
    path_uuid = UUID(wid.removeprefix("instance://"))

    assert (
        client.delete(
            f"/agentic-workflows/{wf_name}/instances/{path_uuid}/",
        ).status_code
        == 202
    )

    event_body = build_instantiate_seed_event(
        _MINIMAL_WORKFLOWS[wf_name],
        wf_name,
        wid,
    )
    r = client.post(
        f"/agentic-workflows/{wf_name}/instances/{path_uuid}/events/",
        json=event_body,
    )
    assert r.status_code == 404


def test_instantiate_twice_delete_one_list_count(
    client: TestClient,
) -> None:
    wf_name = "InstTestWf"
    r1 = client.post(f"/agentic-workflows/{wf_name}/")
    r2 = client.post(f"/agentic-workflows/{wf_name}/")
    assert r1.status_code == 200 and r2.status_code == 200
    wid1 = r1.json()["workflow_instance_id"]
    wid2 = r2.json()["workflow_instance_id"]
    listed = client.get(f"/agentic-workflows/{wf_name}/instances/")
    assert len(listed.json()) == 2

    u1 = UUID(wid1.removeprefix("instance://"))
    assert (
        client.delete(f"/agentic-workflows/{wf_name}/instances/{u1}/").status_code
        == 202
    )
    listed_after = client.get(f"/agentic-workflows/{wf_name}/instances/")
    assert len(listed_after.json()) == 1
    assert wid2 in listed_after.json()
    assert wid1 not in listed_after.json()


def test_post_instantiate_missing_api_key_returns_401(
    app_with_store: FastAPI,
) -> None:
    with patch(_PATCH_GET_WORKFLOWS, return_value=_MINIMAL_WORKFLOWS):
        with TestClient(app_with_store) as bare:
            r = bare.post("/agentic-workflows/InstTestWf/")
    assert r.status_code == 401


def test_post_instantiate_wrong_api_key_returns_401(
    app_with_store: FastAPI,
    workflow_api_headers: dict[str, str],
) -> None:
    bad = {**workflow_api_headers, "Authorization": "Bearer wrong-key"}
    with patch(_PATCH_GET_WORKFLOWS, return_value=_MINIMAL_WORKFLOWS):
        with TestClient(app_with_store, headers=bad) as c:
            r = c.post("/agentic-workflows/InstTestWf/")
    assert r.status_code == 401
