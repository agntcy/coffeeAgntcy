# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Transport-agnostic builders for MCP tool-call topology events.

An MCP tool call is modeled as a transient topology node: a CREATE event when
the tool call starts and a DELETE event when it ends (success or error). The
invoking agent node carries a stable_agent_id so it merges with the same agent
node the A2A middleware emits.
"""

from __future__ import annotations

from typing import Any

from schema.types import (
	Event,
	EventType,
	Operation,
	PartialTopology,
	TopologyEdgeItem,
	TopologyNodeItem,
)

from common.stable_agent_id import stable_agent_id_for_name
from common.workflow_utils.builders import build_event, make_edge, make_node
from common.workflow_utils.event_sink import EventSink
from common.workflow_utils.inflight import RuntimeIdAllocator

MCP_TOOL_NODE_TYPE = "mcp_tool_call"
_AGENT_NODE_TYPE = "customNode"


async def build_mcp_tool_topology(
	agent_id: str,
	tool_name: str,
	mcp_server: str,
	*,
	operation: Operation,
	allocator: RuntimeIdAllocator,
	call_key: str,
	layer_index: int = 0,
	duration_ms: float | None = None,
	error: str | None = None,
	delete_agent_node: bool = False,
) -> PartialTopology:
	"""Build a topology fragment for one MCP tool-call lifecycle event.

	CREATE emits the invoking-agent node, the transient tool-call node
	(carrying tool_name + mcp_server), and the connecting edge. DELETE removes
	the tool-call node and its edge, attaching duration_ms/error when present;
	when ``delete_agent_node`` is set (last in-flight call for this agent) the
	invoking-agent node is removed too so it does not linger in the snapshot.
	"""
	agent_node = await allocator.node_id(f"agent-{agent_id}")
	tool_node = await allocator.node_id(call_key)

	if operation == Operation.CREATE:
		nodes: list[TopologyNodeItem] = [
			make_node(
				agent_node,
				operation=Operation.CREATE,
				node_type=_AGENT_NODE_TYPE,
				label=agent_id,
				layer_index=layer_index,
				stable_agent_id=stable_agent_id_for_name(agent_id),
			),
			make_node(
				tool_node,
				operation=Operation.CREATE,
				node_type=MCP_TOOL_NODE_TYPE,
				label=tool_name,
				layer_index=layer_index + 1,
				extras={"tool_name": tool_name, "mcp_server": mcp_server},
			),
		]
		edges: list[TopologyEdgeItem] = [
			await make_edge(
				agent_node,
				tool_node,
				operation=Operation.CREATE,
				allocator=allocator,
			),
		]
		return PartialTopology(nodes=nodes, edges=edges)

	tool_extras: dict[str, Any] = {}
	if duration_ms is not None:
		tool_extras["duration_ms"] = duration_ms
	if error is not None:
		tool_extras["error"] = error

	nodes = [
		make_node(
			tool_node,
			operation=Operation.DELETE,
			node_type=MCP_TOOL_NODE_TYPE,
			label=tool_name,
			layer_index=layer_index + 1,
			include_size=False,
			extras=tool_extras,
		),
	]
	if delete_agent_node:
		nodes.append(
			make_node(
				agent_node,
				operation=Operation.DELETE,
				node_type=_AGENT_NODE_TYPE,
				label=agent_id,
				layer_index=layer_index,
				include_size=False,
			)
		)
	edges = [
		await make_edge(
			agent_node,
			tool_node,
			operation=Operation.DELETE,
			allocator=allocator,
		),
	]
	return PartialTopology(nodes=nodes, edges=edges)


def _correlation_message(operation: Operation, tool_name: str, mcp_server: str) -> str:
	verb = "start" if operation == Operation.CREATE else "end"
	return f"mcp tool {verb}: {tool_name} on {mcp_server}"


async def emit_mcp_tool_call_event(
	*,
	sink: EventSink,
	source: str,
	agent_id: str,
	tool_name: str,
	mcp_server: str,
	operation: Operation,
	allocator: RuntimeIdAllocator,
	call_key: str,
	correlation_id: str,
	workflow_name: str,
	instance_id: str,
	trace_id: int | None = None,
	span_id: int | None = None,
	layer_index: int = 0,
	duration_ms: float | None = None,
	error: str | None = None,
	delete_agent_node: bool = False,
) -> Event:
	"""Build and emit one MCP tool-call topology event via the sink."""
	topology = await build_mcp_tool_topology(
		agent_id,
		tool_name,
		mcp_server,
		operation=operation,
		allocator=allocator,
		call_key=call_key,
		layer_index=layer_index,
		duration_ms=duration_ms,
		error=error,
		delete_agent_node=delete_agent_node,
	)
	event = build_event(
		source=source,
		workflow_name=workflow_name,
		instance_id=instance_id,
		topology=topology,
		correlation_id=correlation_id,
		event_type=EventType.STATE_PROGRESS_UPDATE,
		correlation_message=_correlation_message(operation, tool_name, mcp_server),
		trace_id=trace_id,
		span_id=span_id,
	)
	await sink.emit(event)
	return event
