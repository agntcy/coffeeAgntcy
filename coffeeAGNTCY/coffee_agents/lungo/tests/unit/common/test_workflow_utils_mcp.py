# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``common.workflow_utils.mcp`` (MCP tool-call builders)."""

from __future__ import annotations

import pytest
from schema.types import Operation

from common.workflow_utils.inflight import RuntimeIdAllocator
from common.workflow_utils.mcp import (
    MCP_TOOL_NODE_TYPE,
    build_mcp_tool_topology,
    emit_mcp_tool_call_event,
)

_AGENT_ID = "Colombia Coffee Farm"
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


def _agent_node(topology):
    for node in topology.nodes:
        if getattr(node, "type", None) != MCP_TOOL_NODE_TYPE:
            return node
    return None


def _tool_node(topology):
    for node in topology.nodes:
        if getattr(node, "type", None) == MCP_TOOL_NODE_TYPE:
            return node
    return None


async def test_build_mcp_tool_topology_create():
    """CREATE builds an agent node, a tool node, and a connecting edge."""
    allocator = RuntimeIdAllocator()
    topology = await build_mcp_tool_topology(
        _AGENT_ID,
        _TOOL,
        _SERVER,
        operation=Operation.CREATE,
        allocator=allocator,
        call_key="call-1",
        layer_index=0,
    )

    assert len(topology.nodes) == 2
    assert len(topology.edges) == 1

    agent_node = _agent_node(topology)
    tool_node = _tool_node(topology)
    assert agent_node.label == _AGENT_ID
    assert getattr(agent_node, "stable_agent_id", None) is not None
    assert tool_node.operation == Operation.CREATE
    assert tool_node.label == _TOOL
    assert tool_node.tool_name == _TOOL
    assert tool_node.mcp_server == _SERVER

    edge = topology.edges[0]
    assert edge.operation == Operation.CREATE
    assert edge.source.root == agent_node.id.root
    assert edge.target.root == tool_node.id.root


@pytest.mark.parametrize(
    "case,duration_ms,error,expect_extras",
    [
        ("with_metrics", 12.5, "boom", True),
        ("without_metrics", None, None, False),
    ],
)
async def test_build_mcp_tool_topology_delete(case, duration_ms, error, expect_extras):
    """DELETE removes the tool node/edge, attaching metrics only when present."""
    allocator = RuntimeIdAllocator()
    topology = await build_mcp_tool_topology(
        _AGENT_ID,
        _TOOL,
        _SERVER,
        operation=Operation.DELETE,
        allocator=allocator,
        call_key="call-1",
        duration_ms=duration_ms,
        error=error,
    )

    assert len(topology.nodes) == 1
    assert len(topology.edges) == 1

    tool_node = _tool_node(topology)
    assert tool_node.operation == Operation.DELETE
    assert topology.edges[0].operation == Operation.DELETE

    if expect_extras:
        assert tool_node.duration_ms == duration_ms
        assert tool_node.error == error
    else:
        assert getattr(tool_node, "duration_ms", None) is None
        assert getattr(tool_node, "error", None) is None


async def test_build_mcp_tool_topology_delete_removes_agent_node():
    """delete_agent_node also tears down the invoking-agent node on the last call."""
    allocator = RuntimeIdAllocator()
    topology = await build_mcp_tool_topology(
        _AGENT_ID,
        _TOOL,
        _SERVER,
        operation=Operation.DELETE,
        allocator=allocator,
        call_key="call-1",
        delete_agent_node=True,
    )

    assert len(topology.nodes) == 2
    agent_node = _agent_node(topology)
    assert agent_node is not None
    assert agent_node.operation == Operation.DELETE
    assert agent_node.label == _AGENT_ID
    assert _tool_node(topology).operation == Operation.DELETE


async def test_create_and_delete_share_tool_node_id():
    """A shared allocator + call_key yields a stable tool node id across events."""
    allocator = RuntimeIdAllocator()
    create = await build_mcp_tool_topology(
        _AGENT_ID, _TOOL, _SERVER,
        operation=Operation.CREATE, allocator=allocator, call_key="call-1",
    )
    delete = await build_mcp_tool_topology(
        _AGENT_ID, _TOOL, _SERVER,
        operation=Operation.DELETE, allocator=allocator, call_key="call-1",
    )
    assert _tool_node(create).id.root == _tool_node(delete).id.root


async def test_emit_mcp_tool_call_event_posts_to_sink():
    """emit_mcp_tool_call_event builds an event and delivers it to the sink."""
    sink = _CapturingSink()
    allocator = RuntimeIdAllocator()

    event = await emit_mcp_tool_call_event(
        sink=sink,
        source="colombia_coffee_farm",
        agent_id=_AGENT_ID,
        tool_name=_TOOL,
        mcp_server=_SERVER,
        operation=Operation.CREATE,
        allocator=allocator,
        call_key="call-1",
        correlation_id="correlation://00000000-0000-4000-8000-000000000004",
        workflow_name="Test Workflow Alpha",
        instance_id="instance://00000000-0000-4000-8000-000000000003",
    )

    assert len(sink.events) == 1
    assert sink.events[0] is event
    assert "Test Workflow Alpha" in event.data.workflows
    assert _TOOL in event.metadata.correlation.message
