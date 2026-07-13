# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for common.mcp_client.call_mcp_tool.

This is the single entry point every Lungo MCP tool call flows through, so the
agntcy-app-sdk contract is asserted here in one place: create_client is
keyword-only, call_tool is invoked as name=/arguments=, and the transport
shared-secret / timeout options behave as documented. Result normalization
(raw vs text, single vs streamed) is covered too.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from common.mcp_client import client as client_mod

_UNSET = object()


class _FakeSession:
    """Async-context MCP session standing in for the agntcy SDK client."""

    def __init__(self, tool_result, tools=None):
        self._tool_result = tool_result
        self._tools = tools or []
        self.call_args = None
        self.list_tools_calls = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def list_tools(self):
        self.list_tools_calls += 1
        return SimpleNamespace(tools=self._tools)

    async def call_tool(self, name, arguments):
        self.call_args = (name, arguments)
        return self._tool_result


def _fake_factory(captured, session):
    """Build a fake AgntcyFactory recording transport/client construction."""

    def create_transport(transport, **kwargs):
        captured["transport_positional"] = transport
        captured["transport_kwargs"] = kwargs
        return "transport-sentinel"

    async def create_client(*, topic=None, transport=None, message_timeout=_UNSET, **extra):
        captured["topic"] = topic
        captured["transport"] = transport
        captured["message_timeout"] = message_timeout
        captured["extra_kwargs"] = extra
        return session

    mcp_accessor = MagicMock()
    mcp_accessor.create_client = create_client

    factory = MagicMock()
    factory.create_transport.side_effect = create_transport
    factory.mcp.return_value = mcp_accessor
    return factory


def _text_result(text):
    return SimpleNamespace(content=[SimpleNamespace(text=text)])


@pytest.fixture(autouse=True)
def _passthrough_wrap():
    """wrap_mcp_client is exercised elsewhere; keep it a no-op here."""
    with patch.object(client_mod, "wrap_mcp_client", side_effect=lambda c, **_: c):
        yield


async def _run(captured, session, **overrides):
    factory = _fake_factory(captured, session)
    kwargs = dict(
        topic="lungo_weather_service",
        tool_name="get_forecast",
        arguments={"location": "colombia"},
        agent_id="Colombia Coffee Farm",
        source="colombia_coffee_farm",
        factory=factory,
    )
    kwargs.update(overrides)
    return await client_mod.call_mcp_tool(**kwargs)


async def test_uses_keyword_create_client_and_call_tool():
    captured = {}
    session = _FakeSession(_text_result("sunny"))

    result = await _run(captured, session)

    assert captured["topic"] == "lungo_weather_service"
    assert captured["transport"] == "transport-sentinel"
    assert captured["extra_kwargs"] == {}
    # call_tool must be invoked as name=/arguments= (the consolidated contract).
    assert session.call_args == ("get_forecast", {"location": "colombia"})
    # Raw result returned when extract_text is not set.
    assert result is session._tool_result


async def test_shared_secret_attached_when_enabled(monkeypatch):
    monkeypatch.setenv("SLIM_SHARED_SECRET", "top-secret")
    captured = {}
    session = _FakeSession(_text_result("sunny"))

    await _run(captured, session, use_shared_secret=True)

    assert captured["transport_kwargs"]["shared_secret_identity"] == "top-secret"


async def test_shared_secret_omitted_when_disabled():
    captured = {}
    session = _FakeSession(_text_result("sunny"))

    await _run(captured, session, use_shared_secret=False)

    assert "shared_secret_identity" not in captured["transport_kwargs"]


async def test_message_timeout_passed_only_when_set():
    captured_default = {}
    await _run(captured_default, _FakeSession(_text_result("x")))
    assert captured_default["message_timeout"] is _UNSET

    captured_set = {}
    await _run(captured_set, _FakeSession(_text_result("x")), message_timeout=45)
    assert captured_set["message_timeout"] == 45


async def test_transport_name_forwarded():
    captured = {}
    await _run(
        captured,
        _FakeSession(_text_result("x")),
        transport_name="default/default/fast_mcp_client",
    )
    assert captured["transport_kwargs"]["name"] == "default/default/fast_mcp_client"


async def test_list_tools_first_lists_before_calling():
    captured = {}
    session = _FakeSession(
        _text_result("sunny"),
        tools=[SimpleNamespace(name="get_forecast")],
    )

    await _run(captured, session, list_tools_first=True)

    assert session.list_tools_calls == 1
    assert session.call_args == ("get_forecast", {"location": "colombia"})


async def test_extract_text_returns_content_text():
    captured = {}
    session = _FakeSession(_text_result("Temperature: 25C"))

    result = await _run(captured, session, extract_text=True)

    assert result == "Temperature: 25C"


async def test_extract_text_handles_missing_content():
    captured = {}
    session = _FakeSession(SimpleNamespace(content=[]))

    result = await _run(captured, session, extract_text=True)

    assert result == "No content returned from tool."


async def test_extract_text_aggregates_streamed_chunks():
    captured = {}

    async def _stream():
        for piece in ("Hello, ", "world"):
            yield SimpleNamespace(
                choices=[SimpleNamespace(delta=SimpleNamespace(content=piece))]
            )

    session = _FakeSession(_stream())

    result = await _run(captured, session, extract_text=True)

    assert result == "Hello, world"
