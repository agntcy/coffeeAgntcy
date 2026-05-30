# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.mcp_servers.utils.invoke_payment_mcp_tool.

These guard the payment MCP client call. The agntcy-app-sdk create_client is
keyword-only, so a positional protocol argument or a mis-named topic keyword
breaks the call before any network activity. The fake client below mirrors the
real keyword-only signature so a regression of that kind would raise TypeError
and fail these tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agents.exceptions import AuthError
from agents.mcp_servers import utils


class _FakeClientSession:
    """Async context manager standing in for an MCP client session."""

    def __init__(self, tool_result):
        self._tool_result = tool_result
        self.called_with = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def call_tool(self, name, arguments):
        self.called_with = (name, arguments)
        return self._tool_result


def _factory_with_recording_client(captured, tool_result):
    """Build a fake AgntcyFactory that records how create_client was called.

    create_client is intentionally keyword-only here to match the real SDK, so
    passing a positional argument (the original bug) would raise TypeError.
    """
    session = _FakeClientSession(tool_result)

    async def create_client(*, url=None, topic=None, transport=None, **kwargs):
        captured["url"] = url
        captured["topic"] = topic
        captured["transport"] = transport
        return session

    mcp_accessor = MagicMock()
    mcp_accessor.create_client = create_client

    factory = MagicMock()
    factory.create_transport.return_value = "transport-sentinel"
    factory.mcp.return_value = mcp_accessor
    return factory, session


@pytest.fixture
def identity_auth_on(monkeypatch):
    monkeypatch.setenv("IDENTITY_AUTH_ENABLED", "true")


async def test_returns_empty_when_identity_auth_disabled(monkeypatch):
    """With identity auth off the tool short-circuits and never builds a client."""
    monkeypatch.delenv("IDENTITY_AUTH_ENABLED", raising=False)

    with patch.object(utils, "AgntcyFactory") as factory_cls:
        result = await utils.invoke_payment_mcp_tool("create_payment")

    assert result == {}
    factory_cls.assert_not_called()


async def test_create_client_uses_keyword_topic(identity_auth_on):
    """The payment client must pass topic as a keyword, with no positional arg."""
    captured = {}
    expected = {"ok": True, "status": "payment created"}
    factory, session = _factory_with_recording_client(captured, expected)

    with patch.object(utils, "AgntcyFactory", return_value=factory):
        result = await utils.invoke_payment_mcp_tool("create_payment")

    # Reaching this point at all proves create_client accepted the call without
    # a positional argument, since the fake signature is keyword-only.
    assert captured["topic"] == "lungo_payment_service"
    assert captured["transport"] == "transport-sentinel"
    assert session.called_with == ("create_payment", {})
    assert result == expected


async def test_authentication_failure_is_wrapped_as_auth_error(identity_auth_on):
    """An unauthorized response is surfaced as AuthError, not the raw exception."""
    captured = {}
    factory, session = _factory_with_recording_client(captured, {})

    async def unauthorized(name, arguments):
        raise RuntimeError("Authentication failed for the payment service")

    session.call_tool = unauthorized

    with patch.object(utils, "AgntcyFactory", return_value=factory):
        with pytest.raises(AuthError):
            await utils.invoke_payment_mcp_tool("list_transactions")
