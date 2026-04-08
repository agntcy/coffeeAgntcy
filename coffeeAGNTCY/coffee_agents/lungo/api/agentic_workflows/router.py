# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""FastAPI router skeleton for the Agentic Workflows API.

Handlers are stubs (501) until store and SSE are implemented.
"""

from __future__ import annotations

from typing import Annotated

from api.agentic_workflows.catalog import (
    PATTERNS,
    USE_CASES,
    get_patterns_dto_response,
    get_use_cases_dto_response,
)
from api.agentic_workflows.dtos import (
    InstantiateWorkflowResponse,
    PatternListResponse,
    UseCaseListResponse,
    WorkflowInstanceMapResponse,
    WorkflowSummary,
    WorkflowSummaryMapResponse,
)
from api.agentic_workflows.workflows import get_starting_workflows
from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import RedirectResponse
from schema.types import Event, Workflow, WorkflowInstance

_TAG = "agentic-workflows"

# FastAPI path params must be scalar types; pattern matches ``InstanceId`` / event_v1 instance_id.
_WORKFLOW_INSTANCE_ID_PATH = r"^instance://[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


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
        return get_patterns_dto_response(PATTERNS)

    @router.get(
        "/use-cases/",
        response_model=UseCaseListResponse,
        summary="List use-cases",
    )
    async def list_use_cases() -> UseCaseListResponse:
        """GET /use-cases/ — catalog of use-cases."""
        return get_use_cases_dto_response(USE_CASES)

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
        all_workflows = get_starting_workflows()

        filtered = all_workflows
        if patterns:
            pattern_set = set(patterns)
            filtered = [w for w in filtered if w["pattern"] in pattern_set]
        if use_cases:
            uc_set = set(use_cases)
            filtered = [w for w in filtered if w["use_case"] in uc_set]

        summary_map = {
            w["name"]: WorkflowSummary(
                name=w["name"],
                pattern=w["pattern"],
                use_case=w["use_case"],
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
        all_workflows = get_starting_workflows()
        wf_dict = next(
            (w for w in all_workflows if w["name"] == workflow_name), None
        )
        if wf_dict is None:
            raise HTTPException(
                status_code=404, detail=f"Workflow not found: {workflow_name}"
            )

        if topology_only:
            return Workflow.model_validate(
                {
                    "pattern": wf_dict["pattern"],
                    "use_case": wf_dict["use_case"],
                    "name": wf_dict["name"],
                    "starting_topology": wf_dict["starting_topology"],
                    "instances": {},
                }
            )

        return Workflow.model_validate(wf_dict)

    @router.post(
        "/agentic-workflows/{workflow_name}/",
        response_model=InstantiateWorkflowResponse,
        summary="Instantiate a workflow",
    )
    async def instantiate_agentic_workflow(
        workflow_name: Annotated[str, Path(min_length=1)],
    ) -> InstantiateWorkflowResponse:
        """POST /agentic-workflows/{workflow_name}/ — new instance id."""
        raise HTTPException(status_code=501, detail="Not implemented")

    @router.get(
        "/agentic-workflows/{workflow_name}/instances/",
        response_model=WorkflowInstanceMapResponse,
        summary="List workflow instances",
    )
    async def list_workflow_instances(
        workflow_name: Annotated[str, Path(min_length=1)],
    ) -> WorkflowInstanceMapResponse:
        """GET instances map keyed by instance id."""
        raise HTTPException(status_code=501, detail="Not implemented")

    @router.get(
        "/agentic-workflows/{workflow_name}/instances/{workflow_instance_id}/",
        response_model=WorkflowInstance,
        summary="Get workflow instance state",
    )
    async def get_workflow_instance_state(
        workflow_name: Annotated[str, Path(min_length=1)],
        workflow_instance_id: Annotated[
            str,
            Path(
                pattern=_WORKFLOW_INSTANCE_ID_PATH,
                description="Workflow instance id (InstanceId URI)",
            ),
        ],
        topology_only: Annotated[bool, Query()] = False,
    ) -> WorkflowInstance:
        """GET instance state; topology_only for projection."""
        raise HTTPException(status_code=501, detail="Not implemented")

    @router.post(
        "/agentic-workflows/{workflow_name}/instances/{workflow_instance_id}/events/",
        status_code=204,
        summary="Post workflow instance event (internal)",
    )
    async def post_workflow_instance_event(
        workflow_name: Annotated[str, Path(min_length=1)],
        workflow_instance_id: Annotated[
            str,
            Path(
                pattern=_WORKFLOW_INSTANCE_ID_PATH,
                description="Workflow instance id (InstanceId URI)",
            ),
        ],
        event: Event,
    ) -> None:
        """POST internal state update event."""
        raise HTTPException(status_code=501, detail="Not implemented")

    @router.get(
        "/agentic-workflows/{workflow_name}/instances/{workflow_instance_id}/events/stream",
        summary="SSE workflow instance events",
    )
    async def stream_workflow_instance_events(
        workflow_name: Annotated[str, Path(min_length=1)],
        workflow_instance_id: Annotated[
            str,
            Path(
                pattern=_WORKFLOW_INSTANCE_ID_PATH,
                description="Workflow instance id (InstanceId URI)",
            ),
        ],
    ) -> None:
        """GET SSE stream; placeholder body until implementation."""
        raise HTTPException(status_code=501, detail="Not implemented")

    return router
