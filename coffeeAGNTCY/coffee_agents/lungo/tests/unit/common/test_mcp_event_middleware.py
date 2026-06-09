# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``common.mcp_event_middleware`` (EventEmittingMCPClient)."""

from __future__ import annotations

import pytest
from schema.types import Operation

from common.mcp_event_middleware import wrap_mcp_client
from common.mcp_event_middleware import wrapper as wrapper_mod
from common.workflow_utils.mcp import MCP_TOOL_NODE_TYPE

_AGENT_ID = "Colombia Coffee Farm"
_SERVER = "lungo_weather_service"
_SOURCE = "colombia_coffee_farm"


class _CapturingSink:
    """Sink stub that records emitted events on the instance."""

    def __init__(self, *args, **kwargs) -> None:
        self.events: list = []

    async def emit(self, event) -> None:
        self.events.append(event)

    async def aclose(self) -> None:
        return None


async def _aiter(items):
    for item in items:
        yield item


async def _aiter_then_raise(items, exc):
    for item in items:
        yield item
    raise exc


class _FakeMCPClient:
    """Duck-typed MCP client used to drive the wrapper."""

    def __init__(self, *, result="ok", stream=None, stream_error=None, error=None) -> None:
        self.result = result
        self.stream = stream
        self.stream_error = stream_error
        self.error = error
        self.calls: list = []
        self.entered = False
        self.exited = False
        self.list_tools_calls = 0

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, *exc_info):
        self.exited = True
        return False

    async def call_tool(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.error is not None:
            raise self.error
        if self.stream is not None:
            if self.stream_error is not None:
                return _aiter_then_raise(self.stream, self.stream_error)
            return _aiter(self.stream)
        return self.result

    async def list_tools(self):
        self.list_tools_calls += 1
        return ["t1", "t2"]


class _StreamThenValueClient:
    """Returns a stream on the first call, a plain value on later calls.

    Lets a streamed call stay in flight (DELETE deferred until iteration)
    while a second call completes, to exercise the agent-node refcount.
    """

    def __init__(self, stream, value) -> None:
        self.stream = stream
        self.value = value
        self.calls = 0

    async def call_tool(self, *args, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return _aiter(self.stream)
        return self.value


@pytest.fixture
def emit_enabled(monkeypatch):
    """Enable emission and route the sink to an in-memory capturer."""
    monkeypatch.setattr(wrapper_mod, "EMIT_WORKFLOW_EVENTS", True, raising=False)
    monkeypatch.setattr(wrapper_mod, "WorkflowAPIEventSink", _CapturingSink, raising=True)


def _instance(event):
    workflow = next(iter(event.data.workflows.values()))
    return next(iter(workflow.instances.values()))


def _node_operations(event):
    return [node.operation for node in _instance(event).topology.nodes]


def _mcp_node(event):
    for node in _instance(event).topology.nodes:
        if getattr(node, "type", None) == MCP_TOOL_NODE_TYPE:
            return node
    return None


def _deleted_agent_node(event):
    for node in _instance(event).topology.nodes:
        is_agent = getattr(node, "type", None) != MCP_TOOL_NODE_TYPE
        if is_agent and node.operation == Operation.DELETE:
            return node
    return None


def _wrap(client):
    return wrap_mcp_client(
        client,
        agent_id=_AGENT_ID,
        mcp_server=_SERVER,
        source=_SOURCE,
    )


@pytest.mark.parametrize(
    "case,args,kwargs",
    [
        ("positional", ("get_forecast",), {}),
        ("name_kwarg", (), {"name": "get_forecast"}),
    ],
)
async def test_call_tool_emits_create_then_delete(case, args, kwargs, emit_enabled):
    """Both call styles forward unchanged and emit CREATE then DELETE."""
    fake = _FakeMCPClient(result="forecast")
    wrapped = _wrap(fake)

    result = await wrapped.call_tool(*args, **kwargs)

    assert result == "forecast"
    assert fake.calls == [(args, kwargs)]

    events = wrapped._event_sink.events
    assert len(events) == 2
    assert Operation.CREATE in _node_operations(events[0])

    create_node = _mcp_node(events[0])
    assert create_node.tool_name == "get_forecast"
    assert create_node.mcp_server == _SERVER

    delete_node = _mcp_node(events[1])
    assert delete_node.operation == Operation.DELETE
    assert getattr(delete_node, "duration_ms", None) is not None
    assert getattr(delete_node, "error", None) is None


async def test_call_tool_error_emits_delete_and_reraises(emit_enabled):
    """A failing tool call still emits DELETE (with error) and re-raises."""
    fake = _FakeMCPClient(error=RuntimeError("boom"))
    wrapped = _wrap(fake)

    with pytest.raises(RuntimeError, match="boom"):
        await wrapped.call_tool("create_payment", {})

    events = wrapped._event_sink.events
    assert len(events) == 2
    delete_node = _mcp_node(events[1])
    assert delete_node.operation == Operation.DELETE
    assert delete_node.error == "boom"
    assert getattr(delete_node, "duration_ms", None) is not None


async def test_call_tool_streaming_delete_after_iteration(emit_enabled):
    """Streamed results emit CREATE up front and DELETE only after iteration."""
    fake = _FakeMCPClient(stream=["a", "b", "c"])
    wrapped = _wrap(fake)

    stream = await wrapped.call_tool(name="get_forecast")
    events = wrapped._event_sink.events
    assert len(events) == 1
    assert Operation.CREATE in _node_operations(events[0])

    chunks = [chunk async for chunk in stream]
    assert chunks == ["a", "b", "c"]
    assert len(events) == 2

    delete_node = _mcp_node(events[1])
    assert delete_node.operation == Operation.DELETE
    assert getattr(delete_node, "error", None) is None


async def test_call_tool_streaming_error_emits_delete_with_error(emit_enabled):
    """Errors raised during streaming surface a DELETE carrying the error."""
    fake = _FakeMCPClient(stream=["a"], stream_error=RuntimeError("midstream"))
    wrapped = _wrap(fake)

    stream = await wrapped.call_tool(name="get_forecast")

    with pytest.raises(RuntimeError, match="midstream"):
        async for _chunk in stream:
            pass

    events = wrapped._event_sink.events
    assert len(events) == 2
    delete_node = _mcp_node(events[1])
    assert delete_node.operation == Operation.DELETE
    assert delete_node.error == "midstream"


async def test_single_call_delete_removes_agent_node(emit_enabled):
    """A lone call drops the in-flight count to zero, so DELETE removes the agent node."""
    fake = _FakeMCPClient(result="forecast")
    wrapped = _wrap(fake)

    await wrapped.call_tool("get_forecast")

    delete_event = wrapped._event_sink.events[1]
    assert _deleted_agent_node(delete_event) is not None


async def test_agent_node_deleted_only_after_last_inflight_call(emit_enabled):
    """With overlapping calls the agent node is removed only when the last ends."""
    fake = _StreamThenValueClient(["x", "y"], "done")
    wrapped = _wrap(fake)

    stream = await wrapped.call_tool("streamer")
    plain = await wrapped.call_tool("quick")
    assert plain == "done"

    # The quick call ends while the stream is still open: no agent-node delete.
    quick_delete = wrapped._event_sink.events[-1]
    assert _mcp_node(quick_delete).operation == Operation.DELETE
    assert _deleted_agent_node(quick_delete) is None

    chunks = [chunk async for chunk in stream]
    assert chunks == ["x", "y"]

    # Stream completion is the last in-flight call: agent node is now removed.
    final_delete = wrapped._event_sink.events[-1]
    assert _deleted_agent_node(final_delete) is not None


async def test_emit_disabled_passthrough(monkeypatch):
    """With emission disabled the wrapper is a transparent passthrough."""
    monkeypatch.setattr(wrapper_mod, "EMIT_WORKFLOW_EVENTS", False, raising=False)
    fake = _FakeMCPClient(result="ok")
    wrapped = _wrap(fake)

    assert wrapped._event_sink is None
    result = await wrapped.call_tool("get_forecast")

    assert result == "ok"
    assert fake.calls == [(("get_forecast",), {})]


async def test_list_tools_passthrough(emit_enabled):
    """Non-call_tool methods delegate to the underlying client, no events."""
    fake = _FakeMCPClient()
    wrapped = _wrap(fake)

    tools = await wrapped.list_tools()

    assert tools == ["t1", "t2"]
    assert fake.list_tools_calls == 1
    assert wrapped._event_sink.events == []


async def test_async_context_manager_delegation(emit_enabled):
    """The wrapper delegates __aenter__/__aexit__ to the wrapped client."""
    fake = _FakeMCPClient(result="ok")

    async with _wrap(fake) as client:
        result = await client.call_tool("get_forecast")

    assert fake.entered is True
    assert fake.exited is True
    assert result == "ok"
    assert len(client._event_sink.events) == 2


async def test_missing_workflow_context_skips_emission(emit_enabled, no_default_baggage):
    """Absent workflow identity skips emission but still runs the tool."""
    fake = _FakeMCPClient(result="ok")
    wrapped = _wrap(fake)

    result = await wrapped.call_tool("get_forecast")

    assert result == "ok"
    assert wrapped._event_sink.events == []
