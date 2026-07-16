# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Cache Lungo UI fields from OASF record annotations and enrich topology JSON."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

_AGENT_UI_BY_STABLE_AGENT_UUID: dict[str, AgentUiEnrichment] = {}


@dataclass(frozen=True)
class AgentUiEnrichment:
    agent_directory_cid: str | None = None
    identity_app_slug: str | None = None
    has_badge_override: bool | None = None
    has_policy_override: bool | None = None
    verification_status_override: str | None = None


def _parse_bool(value: str) -> bool | None:
    lowered = value.strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


def _enrichment_from_annotations(
    annotations: dict[str, Any],
    *,
    agent_label: str,
) -> AgentUiEnrichment:
    cid = annotations.get("lungo.agentDirectoryCid")
    identity = annotations.get("lungo.identityAppSlug")
    badge_raw = annotations.get("lungo.hasBadgeOverride")
    policy_raw = annotations.get("lungo.hasPolicyOverride")
    verification = annotations.get("lungo.verificationStatusOverride")

    has_badge: bool | None = None
    if isinstance(badge_raw, str):
        has_badge = _parse_bool(badge_raw)
        if has_badge is None:
            logger.warning(
                "Invalid lungo.hasBadgeOverride for agent %s: %r",
                agent_label,
                badge_raw,
            )

    has_policy: bool | None = None
    if isinstance(policy_raw, str):
        has_policy = _parse_bool(policy_raw)
        if has_policy is None:
            logger.warning(
                "Invalid lungo.hasPolicyOverride for agent %s: %r",
                agent_label,
                policy_raw,
            )

    verification_status: str | None = None
    if isinstance(verification, str) and verification.strip():
        verification_status = verification.strip().lower()

    return AgentUiEnrichment(
        agent_directory_cid=cid.strip() if isinstance(cid, str) and cid.strip() else None,
        identity_app_slug=(
            identity.strip() if isinstance(identity, str) and identity.strip() else None
        ),
        has_badge_override=has_badge,
        has_policy_override=has_policy,
        verification_status_override=verification_status,
    )


def register_from_record(stable_agent_uuid: str, record: dict) -> None:
    """Parse ``lungo.*`` annotations from a loaded OASF agent record."""
    key = stable_agent_uuid.strip()
    if not key:
        return

    name = record.get("name")
    agent_label = name.strip() if isinstance(name, str) and name.strip() else key

    annotations = record.get("annotations")
    if not isinstance(annotations, dict):
        _AGENT_UI_BY_STABLE_AGENT_UUID[key] = AgentUiEnrichment()
        return

    _AGENT_UI_BY_STABLE_AGENT_UUID[key] = _enrichment_from_annotations(
        annotations,
        agent_label=agent_label,
    )


def lookup_enrichment(stable_agent_uuid: str) -> AgentUiEnrichment | None:
    return _AGENT_UI_BY_STABLE_AGENT_UUID.get(stable_agent_uuid.strip())


def clear_agent_ui_cache() -> None:
    """Test helper: reset cached enrichment."""
    _AGENT_UI_BY_STABLE_AGENT_UUID.clear()


def _stable_agent_uuid_from_wire(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        raw = value.get("root")
    elif hasattr(value, "root"):
        raw = value.root
    else:
        raw = value
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw.strip().removeprefix("agent://").strip() or None


def _merge_enrichment_into_node(node: dict[str, Any]) -> None:
    stable_uuid = _stable_agent_uuid_from_wire(node.get("stable_agent_id"))
    if not stable_uuid:
        return
    enrichment = lookup_enrichment(stable_uuid)
    if enrichment is None:
        return
    if enrichment.agent_directory_cid is not None:
        node["agent_directory_cid"] = enrichment.agent_directory_cid
    if enrichment.identity_app_slug is not None:
        node["identity_app_slug"] = enrichment.identity_app_slug
    if enrichment.has_badge_override is not None:
        node["has_badge_override"] = enrichment.has_badge_override
    if enrichment.has_policy_override is not None:
        node["has_policy_override"] = enrichment.has_policy_override
    if enrichment.verification_status_override is not None:
        node["verification_status_override"] = enrichment.verification_status_override


def enrich_topology_dict(topology: dict[str, Any] | None) -> dict[str, Any]:
    """Return topology with per-node Lungo UI fields merged from the cache."""
    if not topology:
        return {"nodes": [], "edges": []}
    out = dict(topology)
    nodes = out.get("nodes")
    if isinstance(nodes, list):
        enriched_nodes: list[Any] = []
        for node in nodes:
            if isinstance(node, dict):
                node_copy = dict(node)
                _merge_enrichment_into_node(node_copy)
                enriched_nodes.append(node_copy)
            else:
                enriched_nodes.append(node)
        out["nodes"] = enriched_nodes
    return out
