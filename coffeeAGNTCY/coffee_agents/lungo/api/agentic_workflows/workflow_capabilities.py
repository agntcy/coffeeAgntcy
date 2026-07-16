# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Read catalog UI capabilities from workflow metadata."""

from __future__ import annotations

from api.agentic_workflows.catalog_types import ChatApiTarget, parse_chat_api_target
from schema.types import Workflow


def _bool_from_extra(extra: dict[str, object], key: str) -> bool:
    value = extra.get(key)
    if isinstance(value, bool):
        return value
    return False


def derive_workflow_capabilities(
    wf: Workflow,
) -> tuple[bool, bool, ChatApiTarget | None]:
    """Return ``(supports_sse, supports_streaming, chat_api_target)`` from catalog metadata."""
    extra = wf.model_extra or {}
    supports_sse = _bool_from_extra(extra, "supports_sse")
    supports_streaming = _bool_from_extra(extra, "supports_streaming")
    chat_api_target = parse_chat_api_target(extra.get("chat_api_target"))
    return supports_sse, supports_streaming, chat_api_target
