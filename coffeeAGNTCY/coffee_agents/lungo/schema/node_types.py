# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared event_v1 node ``type`` strings (semantic + leftover).

Keep these identical to the frontend ``NODE_TYPE`` values in
``frontend/src/utils/const.ts`` (locked by ``tests/unit/schemas/test_node_types.py``).
Imported by generated ``schema.types.event`` (must stay free of
``schema.types`` / ``common.workflow_utils`` imports).
"""

from __future__ import annotations

AGENT = "agent"
MCP = "mcp"
DIRECTORY = "directory"
GROUP = "group"
TRANSPORT = "transport"
CUSTOM_NODE = "customNode"
TRANSPORT_NODE = "transportNode"

AGENT_EXTENSION_TYPES = frozenset({AGENT, MCP})
BASE_NODE_TYPES = frozenset({TRANSPORT, TRANSPORT_NODE, GROUP, DIRECTORY})
