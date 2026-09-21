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

from api.agentic_workflows.catalog_types import ChatApiTarget


class Pattern(BaseModel):
    """One architectural pattern in the reference library.

    The library is the full set: implemented patterns (at least one runnable
    workflow in the workflow catalog) and reference-only patterns are both
    listed, distinguished by ``implemented``.
    """

    model_config = ConfigDict(extra="forbid")

    name: Annotated[
        str,
        Field(
            min_length=1,
            description="Display name of the pattern (H1 in docs/patterns/{slug}.md).",
        ),
    ]
    pattern_category: Annotated[
        str,
        Field(
            min_length=1,
            description='Agentic design pattern category (e.g. "Orchestration & Control Flow").',
        ),
    ]
    implemented: Annotated[
        bool,
        Field(
            description=(
                "True when the workflow catalog exposes at least one runnable "
                "workflow whose pattern equals this name, false for "
                "reference-only patterns."
            ),
        ),
    ]


class PatternListResponse(BaseModel):
    """Patterns ordered by display name."""

    model_config = ConfigDict(extra="forbid")

    items: list[Pattern]


class PatternDocumentationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: Annotated[
        str,
        Field(
            min_length=1,
            description="Basename slug for docs/patterns/{slug}.md.",
        ),
    ]
    name: Annotated[
        str,
        Field(
            min_length=1,
            description="Display name of the pattern (same as Pattern.name).",
        ),
    ]
    title: Annotated[
        str | None,
        Field(description="Leading H1 from the markdown file, if present."),
    ] = None
    pattern_category: Annotated[
        str,
        Field(
            min_length=1,
            description="Agentic design pattern category for this pattern.",
        ),
    ]
    implemented: Annotated[
        bool,
        Field(
            description=(
                "Same flag as Pattern.implemented, so a doc view can render "
                "without a second call."
            ),
        ),
    ]
    full_markdown: Annotated[
        str,
        Field(description="Full markdown source for the pattern reference doc."),
    ]


class UseCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1)]


class UseCaseListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[UseCase]


class PatternCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1)]


class PatternCategoryListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PatternCategory]


class PatternCategoryDocumentationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: Annotated[
        str,
        Field(
            min_length=1,
            description="Basename slug for docs/categories/{slug}.md.",
        ),
    ]
    name: Annotated[
        str,
        Field(
            min_length=1,
            description="Display name of the category (H1 in the markdown file).",
        ),
    ]
    title: Annotated[
        str | None,
        Field(description="Leading H1 from the markdown file, if present."),
    ] = None
    full_markdown: Annotated[
        str,
        Field(description="Full markdown source for the category reference doc."),
    ]


class WorkflowSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1)]
    pattern: Annotated[str, Field(min_length=1)]
    pattern_category: Annotated[
        str,
        Field(
            min_length=1,
            description='Agentic design pattern category (e.g. "Orchestration & Control Flow").',
        ),
    ]
    use_case: Annotated[str, Field(min_length=1)]
    scenario: Annotated[
        str, Field(min_length=1, description="brief extra qualifier for the use-case")
    ]
    supports_sse: bool
    supports_streaming: bool
    chat_api_target: Annotated[
        ChatApiTarget | None,
        Field(
            description=(
                "Which Lungo chat API base to use; null when the workflow is not "
                "runnable in the UI."
            ),
        ),
    ] = None


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
    pattern_category: Annotated[
        str | None,
        Field(
            description=(
                "Category from the Pattern section (**Category:** line) when present "
                "in the workflow markdown."
            ),
        ),
    ] = None
    sections: list[WorkflowDocumentationSection]
    full_markdown: Annotated[
        str,
        Field(description="Full markdown source for optional single-pass rendering."),
    ]
