# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared derivation of ``stable_agent_id`` from an agent name.

Imported by both the seed-topology loader and the A2A middleware so the same
agent name always yields the same ``agent://<uuid5>`` regardless of which
side emits the node.
"""

from __future__ import annotations

from uuid import NAMESPACE_DNS, UUID, uuid5

STABLE_AGENT_ID_NAMESPACE: UUID = uuid5(
    NAMESPACE_DNS, "agent.workflow.lungo"
)


def stable_agent_uuid_for_name(agent_name: str) -> UUID:
    """Deterministic UUID for an agent name."""
    return uuid5(STABLE_AGENT_ID_NAMESPACE, agent_name)


def stable_agent_id_for_name(agent_name: str) -> str:
    """Deterministic ``agent://<uuid>`` for an agent name."""
    return f"agent://{stable_agent_uuid_for_name(agent_name)!s}"
