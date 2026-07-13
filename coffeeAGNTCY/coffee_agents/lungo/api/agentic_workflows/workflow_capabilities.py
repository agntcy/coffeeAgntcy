# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Derive catalog UI capabilities from workflow topology and name."""

from __future__ import annotations

from api.agentic_workflows.catalog_types import ChatApiTarget
from schema.types import Workflow

_EXCHANGE_WORKFLOW_NAMES = frozenset(
    {"Publish Subscribe", "Publish Subscribe Streaming"},
)


def _topology_has_group_node(wf: Workflow) -> bool:
    for node in wf.starting_topology.nodes:
        node_type = getattr(node, "type", None)
        if isinstance(node_type, str) and node_type.lower() == "group":
            return True
    return False


def derive_workflow_capabilities(
    wf: Workflow,
) -> tuple[bool, bool, ChatApiTarget | None]:
    """Return ``(supports_sse, supports_streaming, chat_api_target)`` for catalog UI."""
    name = wf.name
    supports_sse = _topology_has_group_node(wf)
    supports_streaming = name == "A2A HTTP" or "Streaming" in name

    if supports_sse:
        return supports_sse, supports_streaming, "logistics"
    if name == "A2A HTTP":
        return supports_sse, supports_streaming, "discovery"
    if name in _EXCHANGE_WORKFLOW_NAMES:
        return supports_sse, supports_streaming, "exchange"
    return supports_sse, supports_streaming, None
