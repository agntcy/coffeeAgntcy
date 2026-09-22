# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Python ``schema.node_types`` must match frontend ``NODE_TYPE`` string values."""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

import pytest

import schema.node_types as schema_node_types
from common.workflow_utils import node_types as emitter_node_types

_LUNGO_ROOT = Path(__file__).resolve().parents[3]
_CONST_TS = _LUNGO_ROOT / "frontend" / "src" / "utils" / "const.ts"

_NODE_TYPE_BLOCK = re.compile(
	r"export const NODE_TYPE = \{(?P<body>[^}]+)\}",
	re.MULTILINE,
)
_NODE_TYPE_ENTRY = re.compile(r'(?P<key>\w+):\s*"(?P<value>[^"]+)"')


def frontend_node_type_values() -> dict[str, str]:
	text = _CONST_TS.read_text(encoding="utf-8")
	match = _NODE_TYPE_BLOCK.search(text)
	assert match is not None, f"NODE_TYPE block missing in {_CONST_TS}"
	values: dict[str, str] = {}
	for entry in _NODE_TYPE_ENTRY.finditer(match.group("body")):
		values[entry.group("key")] = entry.group("value")
	return values


class NodeTypeCase(NamedTuple):
	case_id: str
	attr: str
	expected: str


_NODE_TYPE_CASES: tuple[NodeTypeCase, ...] = (
	NodeTypeCase("agent", "AGENT", "agent"),
	NodeTypeCase("mcp", "MCP", "mcp"),
	NodeTypeCase("directory", "DIRECTORY", "directory"),
	NodeTypeCase("group", "GROUP", "group"),
	NodeTypeCase("transport", "TRANSPORT", "transport"),
	NodeTypeCase("custom_node", "CUSTOM_NODE", "customNode"),
	NodeTypeCase("transport_node", "TRANSPORT_NODE", "transportNode"),
)


@pytest.mark.parametrize(
	"case", [pytest.param(c, id=c.case_id) for c in _NODE_TYPE_CASES]
)
def test_schema_and_emitter_node_types_match_frontend(case: NodeTypeCase) -> None:
	frontend = frontend_node_type_values()
	assert getattr(schema_node_types, case.attr) == case.expected
	assert getattr(emitter_node_types, case.attr) == case.expected
	assert frontend[case.attr] == case.expected


def test_node_type_sets_cover_the_shared_strings() -> None:
	assert schema_node_types.AGENT_EXTENSION_TYPES == frozenset(
		{schema_node_types.AGENT, schema_node_types.MCP}
	)
	assert schema_node_types.BASE_NODE_TYPES == frozenset(
		{
			schema_node_types.TRANSPORT,
			schema_node_types.TRANSPORT_NODE,
			schema_node_types.GROUP,
			schema_node_types.DIRECTORY,
		}
	)
	assert emitter_node_types.AGENT_EXTENSION_TYPES is schema_node_types.AGENT_EXTENSION_TYPES
	assert emitter_node_types.BASE_NODE_TYPES is schema_node_types.BASE_NODE_TYPES
	assert set(frontend_node_type_values().values()) == {
		schema_node_types.AGENT,
		schema_node_types.MCP,
		schema_node_types.DIRECTORY,
		schema_node_types.GROUP,
		schema_node_types.TRANSPORT,
		schema_node_types.CUSTOM_NODE,
		schema_node_types.TRANSPORT_NODE,
	}
