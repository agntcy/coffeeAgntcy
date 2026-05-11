# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""FastAPI router for the Agentic Workflows API.

Catalog endpoints, instance/state lifecycle, internal ``POST .../events/``, and SSE stream.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID, uuid4

from api.agentic_workflows.dtos import (
    InstantiateWorkflowResponse,
    Pattern,
    PatternListResponse,
    UseCase,
    UseCaseListResponse,
    WorkflowInstanceMapResponse,
    WorkflowSummary,
    WorkflowSummaryMapResponse,
)
from api.agentic_workflows.instance_lifecycle import (
    build_instantiate_seed_event,
    instances_map_for_workflow,
    workflow_instance_from_store,
)
from api.agentic_workflows.patterns import PATTERNS
from api.agentic_workflows.use_cases import USE_CASES
from api.agentic_workflows.workflows import get_workflows
from common.workflow_instance_store import (
    WorkflowInstanceStateStore,
    WorkflowInstanceStoreClosedError,
)
from fastapi import APIRouter, HTTPException, Path, Query, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from schema import errors as schema_errors
from schema.types import Event, Workflow, WorkflowInstance, instance_id_from_uuid

_TAG = "agentic-workflows"

WORKFLOW_INSTANCE_STORE_ATTR = "workflow_instance_store"

WORKFLOW_INSTANCE_SSE_QUEUE_MAXSIZE = 100
WORKFLOW_INSTANCE_SSE_QUEUE_HIGH_WATER_RATIO = 0.9
WORKFLOW_INSTANCE_SSE_QUEUE_HIGH_WATER = max(
    1,
    int(WORKFLOW_INSTANCE_SSE_QUEUE_MAXSIZE * WORKFLOW_INSTANCE_SSE_QUEUE_HIGH_WATER_RATIO),
)

INSTANTIATE_MERGE_WAIT_TIMEOUT_DETAIL = (
    "Instantiate event was accepted and queued; merge did not finish in time. "
    "Poll list or GET instance state before repeating POST (each POST creates a new instance)."
)


def workflow_instance_event_to_sse_frame(event: Event) -> str:
    """One SSE message: a single ``data:`` line with compact ``event_v1`` JSON (UTF-8 text)."""
    payload = event.model_dump(mode="json", exclude_none=True)
    line = json.dumps(payload, separators=(",", ":"))
    return f"data: {line}\n\n"


def enqueue_workflow_instance_sse_queue_chunk(
    queue: asyncio.Queue[str],
    chunk: str,
    *,
    high_water: int,
) -> None:
    """Append ``chunk`` (SSE frame text, typically JSON ``data:`` lines) to ``queue``.

    At/above ``high_water`` backlog, drop oldest first. If ``put_nowait`` still raises
    :class:`asyncio.QueueFull`, drop oldest and retry until the chunk is queued.
    """
    if queue.qsize() >= high_water and not queue.empty():
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
    while True:
        try:
            queue.put_nowait(chunk)
            return
        except asyncio.QueueFull:
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass


def _workflow_instance_store(request: Request) -> WorkflowInstanceStateStore:
    store = getattr(request.app.state, WORKFLOW_INSTANCE_STORE_ATTR, None)
    if store is None:
        raise HTTPException(
            status_code=503,
            detail="Workflow instance store is not configured",
        )
    return store


def _canonical_instance_uri(instance_uuid: UUID) -> str:
    return instance_id_from_uuid(instance_uuid).root


def create_agentic_workflows_router() -> APIRouter:
    """Build an APIRouter for all agentic-workflows endpoints (single tag)."""
    router = APIRouter(tags=[_TAG])

    @router.get(
        "/",
        summary="Redirect API root to patterns catalog",
        status_code=307,
        response_class=RedirectResponse,
    )
    async def redirect_root_to_patterns() -> RedirectResponse:
        """GET / — redirect to ``/patterns/`` (default route)."""
        return RedirectResponse(url="/patterns/", status_code=307)

    @router.get(
        "/patterns/",
        response_model=PatternListResponse,
        summary="List patterns",
    )
    async def list_patterns() -> PatternListResponse:
        """GET /patterns/ — catalog of patterns."""
        return PatternListResponse(items=[Pattern(name=n) for n in PATTERNS])

    @router.get(
        "/use-cases/",
        response_model=UseCaseListResponse,
        summary="List use-cases",
    )
    async def list_use_cases() -> UseCaseListResponse:
        """GET /use-cases/ — catalog of use-cases."""
        return UseCaseListResponse(items=[UseCase(name=n) for n in USE_CASES])

    @router.get(
        "/agentic-workflows/",
        response_model=WorkflowSummaryMapResponse,
        summary="List workflows",
    )
    async def list_agentic_workflows(
        patterns: Annotated[list[str] | None, Query()] = None,
        use_cases: Annotated[list[str] | None, Query()] = None,
    ) -> WorkflowSummaryMapResponse:
        """GET /agentic-workflows/ — map keyed by workflow name; optional filters."""
        all_workflows = get_workflows()

        filtered = all_workflows.values()
        if patterns:
            pattern_set = set(patterns)
            filtered = [w for w in filtered if w.pattern in pattern_set]
        if use_cases:
            uc_set = set(use_cases)
            filtered = [w for w in filtered if w.use_case in uc_set]

        summary_map = {
            w.name: WorkflowSummary(
                name=w.name,
                pattern=w.pattern,
                use_case=w.use_case,
                scenario=w.scenario,
            )
            for w in filtered
        }
        return WorkflowSummaryMapResponse(summary_map)

    @router.get(
        "/agentic-workflows/{workflow_name}/",
        response_model=Workflow,
        summary="Get workflow details",
    )
    async def get_agentic_workflow(
        workflow_name: Annotated[str, Path(min_length=1)],
        topology_only: Annotated[bool, Query()] = False,
    ) -> Workflow:
        """GET /agentic-workflows/{workflow_name}/ — definition + topology."""
        all_workflows = get_workflows()
        wf = all_workflows.get(workflow_name)
        if wf is None:
            raise HTTPException(
                status_code=404, detail=f"Workflow not found: {workflow_name}"
            )

        if topology_only:
            return wf.model_copy(update={"instances": {}})

        return wf

    @router.post(
        "/agentic-workflows/{workflow_name}/",
        response_model=InstantiateWorkflowResponse,
        summary="Instantiate a workflow",
    )
    async def instantiate_agentic_workflow(
        request: Request,
        workflow_name: Annotated[str, Path(min_length=1)],
    ) -> InstantiateWorkflowResponse:
        """POST /agentic-workflows/{workflow_name}/ — new instance id."""
        all_workflows = get_workflows()
        wf = all_workflows.get(workflow_name)
        if wf is None:
            raise HTTPException(
                status_code=404, detail=f"Workflow not found: {workflow_name}"
            )
        uid = uuid4()
        iid = instance_id_from_uuid(uid)
        iuri = iid.root
        try:
            payload = build_instantiate_seed_event(wf, workflow_name, iuri)
        except ValueError as exc:
            raise HTTPException(
                status_code=500,
                detail="Workflow catalog inconsistency",
            ) from exc
        store = _workflow_instance_store(request)
        try:
            await store.submit_event(payload)
        except schema_errors.SchemaValidationError as exc:
            raise HTTPException(
                status_code=400,
                detail="Event failed schema validation",
            ) from exc
        except WorkflowInstanceStoreClosedError as exc:
            raise HTTPException(
                status_code=503,
                detail="Workflow instance store is closed",
            ) from exc

        try:
            await asyncio.to_thread(store.wait_merge_idle)
        except WorkflowInstanceStoreClosedError as exc:
            raise HTTPException(
                status_code=503,
                detail="Workflow instance store is closed",
            ) from exc
        except TimeoutError as exc:
            raise HTTPException(
                status_code=504,
                detail=INSTANTIATE_MERGE_WAIT_TIMEOUT_DETAIL,
            ) from exc
        return InstantiateWorkflowResponse(workflow_instance_id=iid)

    @router.get(
        "/agentic-workflows/{workflow_name}/instances/",
        response_model=WorkflowInstanceMapResponse,
        summary="List workflow instances",
    )
    async def list_workflow_instances(
        request: Request,
        workflow_name: Annotated[str, Path(min_length=1)],
    ) -> WorkflowInstanceMapResponse:
        """GET instances map keyed by instance id."""
        if workflow_name not in get_workflows():
            raise HTTPException(
                status_code=404, detail=f"Workflow not found: {workflow_name}"
            )
        store = _workflow_instance_store(request)
        data = await asyncio.to_thread(store.get_merged_data)
        items = instances_map_for_workflow(data, workflow_name)
        return WorkflowInstanceMapResponse(items)

    @router.get(
        "/agentic-workflows/{workflow_name}/instances/{workflow_instance_id}/",
        response_model=WorkflowInstance,
        summary="Get workflow instance state",
    )
    async def get_workflow_instance_state(
        request: Request,
        workflow_name: Annotated[str, Path(min_length=1)],
        workflow_instance_id: Annotated[
            UUID,
            Path(
                description=(
                    "Workflow instance UUID (path segment); canonical JSON id is "
                    "instance://{uuid} (InstanceId)."
                ),
            ),
        ],
        topology_only: Annotated[bool, Query()] = False,
    ) -> WorkflowInstance:
        """GET instance state; topology_only for projection."""
        if workflow_name not in get_workflows():
            raise HTTPException(
                status_code=404, detail=f"Workflow not found: {workflow_name}"
            )
        canonical_id = _canonical_instance_uri(workflow_instance_id)
        store = _workflow_instance_store(request)
        try:
            inst = await asyncio.to_thread(
                workflow_instance_from_store,
                store,
                workflow_name,
                canonical_id,
                topology_only=topology_only,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=500,
                detail="Invalid instance projection",
            ) from exc
        if inst is None:
            raise HTTPException(
                status_code=404,
                detail="Workflow instance not found",
            )
        return inst

    @router.post(
        "/agentic-workflows/{workflow_name}/instances/{workflow_instance_id}/events/",
        status_code=204,
        summary="Post workflow instance event (internal)",
    )
    async def post_workflow_instance_event(
        request: Request,
        workflow_name: Annotated[str, Path(min_length=1)],
        workflow_instance_id: Annotated[
            UUID,
            Path(
                description=(
                    "Workflow instance UUID (path segment); canonical JSON id is "
                    "instance://{uuid} (InstanceId)."
                ),
            ),
        ],
        event: Event,
    ) -> None:
        """POST internal state update event."""
        store = _workflow_instance_store(request)
        canonical_id = _canonical_instance_uri(workflow_instance_id)
        if workflow_name not in event.data.workflows:
            raise HTTPException(
                status_code=400,
                detail="Event does not include data for the path workflow_name",
            )
        wf = event.data.workflows[workflow_name]
        if canonical_id not in wf.instances:
            raise HTTPException(
                status_code=400,
                detail="Event does not target the path workflow_instance_id",
            )
        payload = event.model_dump(mode="json", exclude_none=True)
        try:
            await store.submit_event(payload)
        except schema_errors.SchemaValidationError as exc:
            raise HTTPException(
                status_code=400,
                detail="Event failed schema validation",
            ) from exc
        except WorkflowInstanceStoreClosedError as exc:
            raise HTTPException(
                status_code=503,
                detail="Workflow instance store is closed",
            ) from exc

    @router.get(
        "/agentic-workflows/{workflow_name}/instances/{workflow_instance_id}/events/stream",
        summary="SSE workflow instance events",
    )
    async def stream_workflow_instance_events(
        request: Request,
        workflow_name: Annotated[str, Path(min_length=1)],
        workflow_instance_id: Annotated[
            UUID,
            Path(
                description=(
                    "Workflow instance UUID (path segment); canonical JSON id is "
                    "instance://{uuid} (InstanceId)."
                ),
            ),
        ],
    ) -> StreamingResponse:
        """GET SSE stream; each message is one ``data:`` line of compact ``event_v1`` JSON."""
        if workflow_name not in get_workflows():
            raise HTTPException(
                status_code=404, detail=f"Workflow not found: {workflow_name}"
            )
        store = _workflow_instance_store(request)
        canonical_id = _canonical_instance_uri(workflow_instance_id)
        queue: asyncio.Queue[str] = asyncio.Queue(
            maxsize=WORKFLOW_INSTANCE_SSE_QUEUE_MAXSIZE
        )
        loop = asyncio.get_running_loop()

        def listener(ev: Event) -> None:
            if workflow_name not in ev.data.workflows:
                return
            wf_block = ev.data.workflows[workflow_name]
            if canonical_id not in wf_block.instances:
                return
            chunk = workflow_instance_event_to_sse_frame(ev)

            def _enqueue() -> None:
                enqueue_workflow_instance_sse_queue_chunk(
                    queue,
                    chunk,
                    high_water=WORKFLOW_INSTANCE_SSE_QUEUE_HIGH_WATER,
                )

            loop.call_soon_threadsafe(_enqueue)

        unsub = store.subscribe(canonical_id, listener)

        async def event_bytes() -> AsyncIterator[bytes]:
            # Comment frame so ASGI sends response headers before we block on queue.get()
            # (avoids deadlock when another client POSTs the same app in-process).
            yield b":\n\n"
            try:
                while True:
                    frame = await queue.get()
                    yield frame.encode("utf-8")
            finally:
                unsub()

        return StreamingResponse(
            event_bytes(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-store",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return router
