# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared catalog API types for agentic workflows (OpenAPI-aligned)."""

from __future__ import annotations

from typing import Literal

from schema.types import Workflow

ChatApiTarget = Literal["exchange", "logistics", "discovery"]

CHAT_API_TARGETS: frozenset[str] = frozenset({"exchange", "logistics", "discovery"})


def parse_chat_api_target(raw: object) -> ChatApiTarget | None:
    """Return a validated ``chat_api_target`` from catalog metadata, or ``None``."""
    if isinstance(raw, str) and raw in CHAT_API_TARGETS:
        return raw  # type: ignore[return-value]
    return None


def chat_api_target_from_workflow(wf: Workflow) -> ChatApiTarget | None:
    """Read ``chat_api_target`` from ``Workflow.model_extra``."""
    extra = wf.model_extra or {}
    return parse_chat_api_target(extra.get("chat_api_target"))
