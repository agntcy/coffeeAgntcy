# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Resolve deployment message transport facts and enrich transport topology nodes."""

from __future__ import annotations

from typing import Any

from api.agentic_workflows.catalog_types import ChatApiTarget
from config.config import DEFAULT_MESSAGE_TRANSPORT

_TRANSPORT_BY_TARGET: dict[ChatApiTarget, str] = {}

_ENRICHABLE_TARGETS: frozenset[ChatApiTarget] = frozenset({"exchange", "logistics"})


def init_transport_cache() -> None:
    """Populate transport facts from lungo deployment config (v1: no HTTP fetch)."""
    _TRANSPORT_BY_TARGET.clear()
    _TRANSPORT_BY_TARGET["exchange"] = DEFAULT_MESSAGE_TRANSPORT.upper()
    _TRANSPORT_BY_TARGET["logistics"] = "SLIM"


def clear_transport_cache() -> None:
    """Test helper: reset cached transport facts."""
    _TRANSPORT_BY_TARGET.clear()


def resolve_message_transport(chat_api_target: ChatApiTarget | None) -> str | None:
    if chat_api_target is None:
        return None
    return _TRANSPORT_BY_TARGET.get(chat_api_target)


def _transport_node_type(node: dict[str, Any]) -> bool:
    node_type = node.get("type")
    if node_type is None:
        return False
    if isinstance(node_type, str):
        return node_type == "transportNode"
    if hasattr(node_type, "root"):
        return node_type.root == "transportNode"
    return False


def enrich_topology_transport(
    topology: dict[str, Any],
    *,
    chat_api_target: ChatApiTarget | None,
) -> dict[str, Any]:
    """For each ``transportNode``, set ``message_transport`` and display ``label``."""
    if chat_api_target not in _ENRICHABLE_TARGETS:
        return topology

    message_transport = resolve_message_transport(chat_api_target)
    if not message_transport:
        return topology

    out = dict(topology)
    nodes = out.get("nodes")
    if not isinstance(nodes, list):
        return out

    enriched_nodes: list[Any] = []
    for node in nodes:
        if not isinstance(node, dict) or not _transport_node_type(node):
            enriched_nodes.append(node)
            continue
        node_copy = dict(node)
        node_copy["message_transport"] = message_transport
        node_copy["label"] = f"Transport: {message_transport}"
        enriched_nodes.append(node_copy)

    out["nodes"] = enriched_nodes
    return out
