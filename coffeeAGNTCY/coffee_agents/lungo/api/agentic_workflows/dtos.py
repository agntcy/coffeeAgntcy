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
    scenario: Annotated[str, Field(min_length=1, description="brief extra qualifier for the use-case")]


class WorkflowSummaryMapResponse(RootModel[dict[str, WorkflowSummary]]):
    """Workflows keyed by workflow name (see OpenAPI ``WorkflowSummaryMapResponse``)."""


class InstantiateWorkflowResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_instance_id: InstanceId


class WorkflowInstanceMapResponse(RootModel[dict[str, WorkflowInstance]]):
    """Instances keyed by ``InstanceId`` string (see OpenAPI ``WorkflowInstanceMapResponse``)."""

class WorkflowDocumentationSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    anchor: Annotated[str, Field(min_length=1)]
    heading: Annotated[str, Field(min_length=1)]
    body_markdown: Annotated[
        str,
        Field(
            description="Markdown fragment for this section (content below the ## heading).",
        ),
    ]


class PatternChatRequest(BaseModel):
    """Body of ``POST /patterns/{name}/chat``.

    The server holds per-session conversation state and the pattern reference
    markdown in memory, keyed by ``(pattern_name, session_id)``. The client mints
    ``session_id`` once per conversation and resends it each turn; the latest user
    turn is sent in ``message``.
    """

    model_config = ConfigDict(extra="forbid")

    session_id: Annotated[
        str,
        Field(
            pattern=(
                r"^session://[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
                r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
            ),
            description=(
                "Client-minted opaque conversation id, a UUIDv4 wrapped as a "
                "session URI (e.g. session://<uuid>)."
            ),
        ),
    ]
    message: Annotated[
        str,
        Field(
            min_length=1,
            max_length=32 * 1024,
            description="Latest user turn. Server holds the rest of the conversation.",
        ),
    ]


class WorkflowDocumentationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: Annotated[
        str,
        Field(
            min_length=1,
            description="Basename slug used to load docs/workflows/{slug}.md.",
        ),
    ]
    workflow_name: Annotated[
        str,
        Field(
            min_length=1,
            description="Catalog workflow name (same as URL path segment).",
        ),
    ]
    title: Annotated[
        str | None,
        Field(description="Leading H1 from the markdown file, if present."),
    ] = None
    sections: list[WorkflowDocumentationSection]
    full_markdown: Annotated[
        str,
        Field(description="Full markdown source for optional single-pass rendering."),
    ]
