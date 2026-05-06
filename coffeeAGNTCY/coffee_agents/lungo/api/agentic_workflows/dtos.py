# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Catalog and list DTOs for the agentic workflows HTTP API.

These models are **temporary** API-layer types used until catalog contracts stabilize
(GitHub #468). They should be **integrated into the canonical JSON Schema** under
``schema/jsonschemas/`` and mirrored in ``schema/types/`` so OpenAPI, JSON Schema,
and Pydantic stay a single source of truth.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel
from schema.types import InstanceId, WorkflowInstance


class Pattern(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1)]


class PatternListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[Pattern]


class UseCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1)]


class UseCaseListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[UseCase]


class WorkflowSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1)]
    pattern: Annotated[str, Field(min_length=1)]
    use_case: Annotated[str, Field(min_length=1)]


class WorkflowSummaryMapResponse(RootModel[dict[str, WorkflowSummary]]):
    """Workflows keyed by workflow name (see OpenAPI ``WorkflowSummaryMapResponse``)."""


class InstantiateWorkflowResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_instance_id: InstanceId


class WorkflowInstanceMapResponse(RootModel[dict[str, WorkflowInstance]]):
    """Instances keyed by ``InstanceId`` string (see OpenAPI ``WorkflowInstanceMapResponse``)."""
