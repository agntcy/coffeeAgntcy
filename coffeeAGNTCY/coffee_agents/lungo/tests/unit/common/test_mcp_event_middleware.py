# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``common.mcp_event_middleware`` (EventEmittingMCPClient)."""

from __future__ import annotations

import pytest
from schema.types import Operation

from common.mcp_event_middleware import wrap_mcp_client
from common.mcp_event_middleware import wrapper as wrapper_mod
from common.stable_agent_id import stable_agent_id_for_name
from common.workflow_context_prop import (
    attach_workflow_context,
    detach_workflow_context,
)

_AGENT_ID = "Colombia Coffee Farm"
_TARGET_SID = stable_agent_id_for_name("Weather MCP Server")
_SERVER = "lungo_weather_service"
_SOURCE = "colombia_coffee_farm"
_WORKFLOW_NAME = "Test Workflow Alpha"
_INSTANCE_ID = "instance://00000000-0000-4000-8000-000000000001"


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


class _DistinctSession:
    """Session object yielded by a context manager (exposes call_tool)."""

    def __init__(self, result="ok") -> None:
        self.result = result
        self.calls: list = []
        self.session_exited = False

    async def call_tool(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.result

    async def __aexit__(self, *exc_info):
        self.session_exited = True
        return False


class _DistinctSessionClient:
    """Context manager whose __aenter__ yields a distinct session object."""

    def __init__(self, session: _DistinctSession) -> None:
        self._session = session
        self.entered = False
        self.cm_exited = False

    async def __aenter__(self):
        self.entered = True
        return self._session

    async def __aexit__(self, *exc_info):
        self.cm_exited = True
        return False


@pytest.fixture
def emit_enabled(monkeypatch):
    """Enable emission and route the sink to an in-memory capturer."""
    monkeypatch.setattr(wrapper_mod, "EMIT_WORKFLOW_EVENTS", True, raising=False)
    monkeypatch.setattr(wrapper_mod, "WorkflowAPIEventSink", _CapturingSink, raising=True)


def _instance(event):
    workflow = next(iter(event.data.workflows.values()))
    return next(iter(workflow.instances.values()))


def _edge(event):
    topology = _instance(event).topology
    assert topology.edges
    return topology.edges[0]


def _wrap(client):
    return wrap_mcp_client(
        client,
        agent_id=_AGENT_ID,
        mcp_server=_SERVER,
        target_stable_agent_id=_TARGET_SID,
        source=_SOURCE,
    )


@pytest.mark.parametrize(
    "case,args,kwargs",
    [
        ("positional", ("get_forecast",), {}),
        ("name_kwarg", (), {"name": "get_forecast"}),
    ],
)
async def test_call_tool_emits_start_then_end(case, args, kwargs, emit_enabled):
    """Both call styles emit edge UPDATE start then end events."""
    fake = _FakeMCPClient(result="forecast")
    wrapped = _wrap(fake)

    result = await wrapped.call_tool(*args, **kwargs)

    assert result == "forecast"
    assert fake.calls == [(args, kwargs)]

    events = wrapped._event_sink.events
    assert len(events) == 2

    start_edge = _edge(events[0])
    assert start_edge.operation == Operation.UPDATE
    assert start_edge.mcp_in_flight is True
    assert start_edge.tool_name == "get_forecast"
    assert start_edge.mcp_server == _SERVER
    assert start_edge.source_stable_agent_id == stable_agent_id_for_name(_AGENT_ID)
    assert start_edge.target_stable_agent_id == _TARGET_SID

    end_edge = _edge(events[1])
    assert end_edge.operation == Operation.UPDATE
    assert end_edge.mcp_in_flight is False
    assert _instance(events[0]).topology.nodes == []
    assert _instance(events[1]).topology.nodes == []


async def test_call_tool_error_emits_end_and_reraises(emit_enabled):
    """A failing tool call still emits end and re-raises."""
    fake = _FakeMCPClient(error=RuntimeError("boom"))
    wrapped = _wrap(fake)

    with pytest.raises(RuntimeError, match="boom"):
        await wrapped.call_tool("create_payment", {})

    events = wrapped._event_sink.events
    assert len(events) == 2
    assert _edge(events[1]).mcp_in_flight is False


async def test_call_tool_streaming_end_after_iteration(emit_enabled):
    """Streamed results emit start up front and end only after iteration."""
    fake = _FakeMCPClient(stream=["a", "b", "c"])
    wrapped = _wrap(fake)

    stream = await wrapped.call_tool(name="get_forecast")
    events = wrapped._event_sink.events
    assert len(events) == 1
    assert _edge(events[0]).mcp_in_flight is True

    chunks = [chunk async for chunk in stream]
    assert chunks == ["a", "b", "c"]
    assert len(events) == 2
    assert _edge(events[1]).mcp_in_flight is False


async def test_call_tool_streaming_error_emits_end(emit_enabled):
    """Errors raised during streaming still emit end."""
    fake = _FakeMCPClient(stream=["a"], stream_error=RuntimeError("midstream"))
    wrapped = _wrap(fake)

    stream = await wrapped.call_tool(name="get_forecast")

    with pytest.raises(RuntimeError, match="midstream"):
        async for _chunk in stream:
            pass

    events = wrapped._event_sink.events
    assert len(events) == 2
    assert _edge(events[1]).mcp_in_flight is False


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


async def test_aexit_targets_context_manager_not_session(emit_enabled):
    """Regression: __aexit__ must close the context manager, not the session."""
    session = _DistinctSession(result="forecast")
    cm = _DistinctSessionClient(session)

    async with _wrap(cm) as client:
        result = await client.call_tool("get_forecast")

    assert result == "forecast"
    assert session.calls == [(("get_forecast",), {})]
    assert cm.entered is True
    assert cm.cm_exited is True
    assert session.session_exited is False
    assert len(client._event_sink.events) == 2


async def test_emit_disabled_returns_unwrapped(monkeypatch):
    """With emission disabled the original client is returned unwrapped."""
    monkeypatch.setattr(wrapper_mod, "EMIT_WORKFLOW_EVENTS", False, raising=False)
    fake = _FakeMCPClient(result="ok")
    wrapped = _wrap(fake)

    assert wrapped is fake
    result = await wrapped.call_tool("get_forecast")

    assert result == "ok"
    assert fake.calls == [(("get_forecast",), {})]


async def test_missing_workflow_context_returns_unwrapped(emit_enabled, no_default_baggage):
    """Absent workflow identity returns the unwrapped client (no events)."""
    fake = _FakeMCPClient(result="ok")
    wrapped = _wrap(fake)

    assert wrapped is fake
    result = await wrapped.call_tool("get_forecast")

    assert result == "ok"
    assert fake.calls == [(("get_forecast",), {})]


async def test_explicit_identity_used_when_baggage_absent(emit_enabled, no_default_baggage):
    """With no baggage, explicit workflow_name/instance_id resolve identity."""
    fake = _FakeMCPClient(result="forecast")
    wrapped = wrap_mcp_client(
        fake,
        agent_id=_AGENT_ID,
        mcp_server=_SERVER,
        target_stable_agent_id=_TARGET_SID,
        source=_SOURCE,
        workflow_name=_WORKFLOW_NAME,
        instance_id=_INSTANCE_ID,
    )

    assert wrapped is not fake
    result = await wrapped.call_tool("get_forecast")

    assert result == "forecast"
    assert len(wrapped._event_sink.events) == 2


async def test_explicit_fallback_when_baggage_unknown(emit_enabled, no_default_baggage):
    """Baggage present but unknown to the catalog falls through to explicit."""
    token = attach_workflow_context(
        workflow_name="Unknown Workflow",
        workflow_instance_id="instance://00000000-0000-4000-8000-000000000099",
    )
    try:
        fake = _FakeMCPClient(result="ok")
        wrapped = wrap_mcp_client(
            fake,
            agent_id=_AGENT_ID,
            mcp_server=_SERVER,
            target_stable_agent_id=_TARGET_SID,
            source=_SOURCE,
            workflow_name=_WORKFLOW_NAME,
            instance_id=_INSTANCE_ID,
        )

        assert wrapped is not fake
        await wrapped.call_tool("get_forecast")
        assert len(wrapped._event_sink.events) == 2
    finally:
        detach_workflow_context(token)
