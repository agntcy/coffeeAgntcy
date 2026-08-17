# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Transport-agnostic builders for MCP tool-call edge topology events.

An MCP tool call is modeled as an UPDATE on an existing catalog edge between
the invoking agent and the MCP server node. Emitters carry ``stable_agent_id``
endpoint pairs; the merge layer resolves live ``edge://`` ids server-side.
"""

from __future__ import annotations

from uuid import uuid4

from schema.types import (
	EdgeId,
	Event,
	EventType,
	Operation,
	PartialEdge,
	PartialTopology,
)

from common.stable_agent_id import stable_agent_id_for_name
from common.workflow_utils.builders import build_event
from common.workflow_utils.event_sink import EventSink


def build_mcp_edge_topology(
	agent_id: str,
	tool_name: str,
	mcp_server: str,
	target_stable_agent_id: str,
	*,
	mcp_in_flight: bool,
) -> PartialTopology:
	"""Build a topology fragment for one MCP tool-call edge event.

	Emits a single edge UPDATE keyed by ``source_stable_agent_id`` and
	``target_stable_agent_id`` extras. The workflow API reconcile step
	replaces the placeholder edge id with the live catalog edge id.
	"""
	source_stable_agent_id = stable_agent_id_for_name(agent_id)
	return PartialTopology(
		nodes=[],
		edges=[
			PartialEdge(
				id=EdgeId(f"edge://{uuid4()}"),
				operation=Operation.UPDATE,
				source_stable_agent_id=source_stable_agent_id,
				target_stable_agent_id=target_stable_agent_id,
				tool_name=tool_name,
				mcp_server=mcp_server,
				mcp_in_flight=mcp_in_flight,
			),
		],
	)


def _correlation_message(mcp_in_flight: bool, tool_name: str, mcp_server: str) -> str:
	verb = "start" if mcp_in_flight else "end"
	return f"mcp tool {verb}: {tool_name} on {mcp_server}"


async def emit_mcp_edge_event(
	*,
	sink: EventSink,
	source: str,
	agent_id: str,
	tool_name: str,
	mcp_server: str,
	target_stable_agent_id: str,
	mcp_in_flight: bool,
	correlation_id: str,
	workflow_name: str,
	instance_id: str,
	trace_id: int | None = None,
	span_id: int | None = None,
) -> Event:
	"""Build and emit one MCP edge topology event via the sink."""
	topology = build_mcp_edge_topology(
		agent_id,
		tool_name,
		mcp_server,
		target_stable_agent_id,
		mcp_in_flight=mcp_in_flight,
	)
	event = build_event(
		source=source,
		workflow_name=workflow_name,
		instance_id=instance_id,
		topology=topology,
		correlation_id=correlation_id,
		event_type=EventType.STATE_PROGRESS_UPDATE,
		correlation_message=_correlation_message(mcp_in_flight, tool_name, mcp_server),
		trace_id=trace_id,
		span_id=span_id,
	)
	await sink.emit(event)
	return event
