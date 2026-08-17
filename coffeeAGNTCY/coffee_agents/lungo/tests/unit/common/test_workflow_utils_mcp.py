# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``common.workflow_utils.mcp`` (MCP edge builders)."""

from __future__ import annotations

import pytest
from schema.types import Operation

from common.stable_agent_id import stable_agent_id_for_name
from common.workflow_utils.mcp import (
	build_mcp_edge_topology,
	emit_mcp_edge_event,
)

_AGENT_ID = "Colombia Coffee Farm"
_TARGET_SID = stable_agent_id_for_name("Weather MCP Server")
_TOOL = "get_forecast"
_SERVER = "lungo_weather_service"


class _CapturingSink:
	"""In-memory EventSink for asserting emitted events."""

	def __init__(self) -> None:
		self.events: list = []

	async def emit(self, event) -> None:
		self.events.append(event)

	async def aclose(self) -> None:
		return None


@pytest.mark.parametrize(
	"case,mcp_in_flight",
	[
		("start", True),
		("end", False),
	],
)
def test_build_mcp_edge_topology(case, mcp_in_flight):
	"""Edge-only topology carries stable ids and mcp_in_flight flag."""
	topology = build_mcp_edge_topology(
		_AGENT_ID,
		_TOOL,
		_SERVER,
		_TARGET_SID,
		mcp_in_flight=mcp_in_flight,
	)

	assert topology.nodes == []
	assert len(topology.edges) == 1

	edge = topology.edges[0]
	assert edge.operation == Operation.UPDATE
	assert edge.source_stable_agent_id == stable_agent_id_for_name(_AGENT_ID)
	assert edge.target_stable_agent_id == _TARGET_SID
	assert edge.tool_name == _TOOL
	assert edge.mcp_server == _SERVER
	assert edge.mcp_in_flight is mcp_in_flight
	assert edge.id.root.startswith("edge://")


async def test_emit_mcp_edge_event_posts_to_sink():
	"""emit_mcp_edge_event builds an event and delivers it to the sink."""
	sink = _CapturingSink()

	event = await emit_mcp_edge_event(
		sink=sink,
		source="colombia_coffee_farm",
		agent_id=_AGENT_ID,
		tool_name=_TOOL,
		mcp_server=_SERVER,
		target_stable_agent_id=_TARGET_SID,
		mcp_in_flight=True,
		correlation_id="correlation://00000000-0000-4000-8000-000000000004",
		workflow_name="Test Workflow Alpha",
		instance_id="instance://00000000-0000-4000-8000-000000000003",
	)

	assert len(sink.events) == 1
	assert sink.events[0] is event
	assert "Test Workflow Alpha" in event.data.workflows
	assert _TOOL in event.metadata.correlation.message
	assert event.data.workflows["Test Workflow Alpha"].instances[
		"instance://00000000-0000-4000-8000-000000000003"
	].topology.edges[0].mcp_in_flight is True
