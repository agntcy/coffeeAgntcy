# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""POST workflow-instance events and SSE stream (event_v1 contract)."""

from __future__ import annotations

import asyncio
import json
from uuid import UUID

import pytest
from api.agentic_workflows.router import (
    WORKFLOW_INSTANCE_STORE_ATTR,
    WORKFLOW_INSTANCE_SSE_QUEUE_HIGH_WATER_RATIO,
    create_agentic_workflows_router,
    enqueue_workflow_instance_sse_queue_chunk,
    workflow_instance_event_to_sse_frame,
)
from common.workflow_instance_store import WorkflowInstanceStateStore
from fastapi import FastAPI
from fastapi.testclient import TestClient
from schema.types import Event, instance_id_from_uuid


def _event_dict(workflow_name: str, instance_uri: str, event_id: str) -> dict:
    return {
        "metadata": {
            "timestamp": "2026-01-01T00:00:00Z",
            "schema_version": "1.0.0",
            "correlation": {"id": "correlation://550e8400-e29b-41d4-a716-446655440001"},
            "id": event_id,
            "type": "StateProgressUpdate",
            "source": "test",
        },
        "data": {
            "workflows": {
                workflow_name: {
                    "name": workflow_name,
                    "pattern": "p",
                    "use_case": "u",
                    "scenario": "s",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        instance_uri: {
                            "id": instance_uri,
                            "topology": {},
                        }
                    },
                }
            }
        },
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
def client(app_with_store: FastAPI) -> TestClient:
    with TestClient(app_with_store) as c:
        yield c


def test_post_workflow_instance_event_valid_returns_204(
    client: TestClient,
) -> None:
    uid = UUID("550e8400-e29b-41d4-a716-446655440010")
    iuri = instance_id_from_uuid(uid).root
    wf = "post_wf"
    body = _event_dict(wf, iuri, "event://550e8400-e29b-41d4-a716-446655440011")
    r = client.post(
        f"/agentic-workflows/{wf}/instances/{uid}/events/",
        json=body,
    )
    assert r.status_code == 204


def test_post_workflow_instance_event_wrong_workflow_returns_400(
    client: TestClient,
) -> None:
    uid = UUID("550e8400-e29b-41d4-a716-446655440020")
    iuri = instance_id_from_uuid(uid).root
    body = _event_dict("only_in_body", iuri, "event://550e8400-e29b-41d4-a716-446655440021")
    r = client.post(
        "/agentic-workflows/path_wf/instances/{}/events/".format(uid),
        json=body,
    )
    assert r.status_code == 400


def test_post_workflow_instance_event_wrong_instance_returns_400(
    client: TestClient,
) -> None:
    uid_path = UUID("550e8400-e29b-41d4-a716-446655440030")
    other = "instance://550e8400-e29b-41d4-a716-446655440031"
    wf = "mismatch_wf"
    body = _event_dict(wf, other, "event://550e8400-e29b-41d4-a716-446655440032")
    r = client.post(
        f"/agentic-workflows/{wf}/instances/{uid_path}/events/",
        json=body,
    )
    assert r.status_code == 400


def test_post_workflow_instance_event_invalid_body_returns_422(
    client: TestClient,
) -> None:
    uid = UUID("550e8400-e29b-41d4-a716-446655440040")
    r = client.post(
        f"/agentic-workflows/w/instances/{uid}/events/",
        json={"metadata": {}, "data": {}},
    )
    assert r.status_code == 422


def test_workflow_instance_event_to_sse_frame_roundtrips_event_v1() -> None:
    uid = UUID("550e8400-e29b-41d4-a716-4466554400aa")
    iuri = instance_id_from_uuid(uid).root
    wf_name = "sse_wf"
    body = _event_dict(wf_name, iuri, "event://550e8400-e29b-41d4-a716-4466554400ab")
    ev = Event.model_validate(body)
    frame = workflow_instance_event_to_sse_frame(ev)
    assert frame.startswith("data:")
    first_line = frame.split("\n", 1)[0]
    json_part = first_line[len("data:") :].strip()
    Event.model_validate(json.loads(json_part))


def _sse_high_water(maxsize: int) -> int:
    return max(1, int(maxsize * WORKFLOW_INSTANCE_SSE_QUEUE_HIGH_WATER_RATIO))


def test_sse_path_workflow_filter_skips_when_event_has_other_workflow_key() -> None:
    """Mirrors the stream listener guard: path ``workflow_name`` must exist on ``event.data.workflows``."""
    uid = UUID("550e8400-e29b-41d4-a716-4466554400e0")
    path_wf = "path_wf"
    body_wf = "body_wf"
    iuri = instance_id_from_uuid(uid).root
    ev = Event.model_validate(
        _event_dict(body_wf, iuri, "event://550e8400-e29b-41d4-a716-4466554400e1")
    )
    assert body_wf in ev.data.workflows
    assert path_wf not in ev.data.workflows


def test_enqueue_workflow_instance_sse_queue_chunk_drops_oldest_at_high_water() -> None:
    maxsize = 10
    high_water = _sse_high_water(maxsize)
    q: asyncio.Queue[str] = asyncio.Queue(maxsize=maxsize)
    for i in range(high_water):
        enqueue_workflow_instance_sse_queue_chunk(
            q, str(i), high_water=high_water
        )
    assert q.qsize() == high_water
    enqueue_workflow_instance_sse_queue_chunk(
        q, "newest", high_water=high_water
    )
    assert q.qsize() == high_water
    drained = [q.get_nowait() for _ in range(high_water)]
    assert "0" not in drained
    assert drained[-1] == "newest"


def test_post_event_updates_merged_store(
    client: TestClient,
    app_with_store: FastAPI,
) -> None:
    store = getattr(app_with_store.state, WORKFLOW_INSTANCE_STORE_ATTR)
    uid = UUID("550e8400-e29b-41d4-a716-4466554400bb")
    iuri = instance_id_from_uuid(uid).root
    wf_name = "merge_wf"
    body = _event_dict(wf_name, iuri, "event://550e8400-e29b-41d4-a716-4466554400bc")
    r = client.post(
        f"/agentic-workflows/{wf_name}/instances/{uid}/events/",
        json=body,
    )
    assert r.status_code == 204
    store.wait_merge_idle()
    merged = store.get_merged_data().model_dump(mode="python")
    assert wf_name in merged["workflows"]
    assert iuri in merged["workflows"][wf_name]["instances"]


def test_create_agentic_workflows_app_attaches_store() -> None:
    from api.agentic_workflows.server import create_agentic_workflows_app

    app = create_agentic_workflows_app()
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        store = getattr(app.state, WORKFLOW_INSTANCE_STORE_ATTR)
        assert isinstance(store, WorkflowInstanceStateStore)
