# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.mcp_servers.utils.invoke_payment_mcp_tool.

Guards the payment MCP client call. agntcy-app-sdk create_client is keyword-only;
a positional protocol arg or wrong topic keyword breaks before any network activity.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from agents.exceptions import AuthError
from agents.mcp_servers import utils

_AGENT_ID = "Colombia Coffee Farm"
_SOURCE = "colombia_coffee_farm"


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
    """Fake AgntcyFactory that records how create_client was called."""
    session = _FakeClientSession(tool_result)

    async def create_client(*, topic=None, transport=None, **kwargs):
        captured["topic"] = topic
        captured["transport"] = transport
        captured["extra_kwargs"] = kwargs
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
    monkeypatch.delenv("IDENTITY_AUTH_ENABLED", raising=False)

    with patch.object(utils, "AgntcyFactory") as factory_cls:
        result = await utils.invoke_payment_mcp_tool(
            "create_payment",
            agent_id=_AGENT_ID,
            source=_SOURCE,
        )

    assert result == {}
    factory_cls.assert_not_called()


async def test_create_client_uses_keyword_topic(identity_auth_on):
    captured = {}
    expected = {"ok": True, "status": "payment created"}
    factory, session = _factory_with_recording_client(captured, expected)

    with (
        patch.object(utils, "AgntcyFactory", return_value=factory),
        patch.object(utils, "wrap_mcp_client", side_effect=lambda client, **_: client),
    ):
        result = await utils.invoke_payment_mcp_tool(
            "create_payment",
            agent_id=_AGENT_ID,
            source=_SOURCE,
        )

    assert captured["topic"] == "lungo_payment_service"
    assert captured["transport"] == "transport-sentinel"
    assert captured["extra_kwargs"] == {}
    assert session.called_with == ("create_payment", {})
    assert result == expected


async def test_authentication_failure_is_wrapped_as_auth_error(identity_auth_on):
    factory, session = _factory_with_recording_client({}, {})

    async def unauthorized(name, arguments):
        raise RuntimeError("Authentication failed for the payment service")

    session.call_tool = unauthorized

    with (
        patch.object(utils, "AgntcyFactory", return_value=factory),
        patch.object(utils, "wrap_mcp_client", side_effect=lambda client, **_: client),
    ):
        with pytest.raises(AuthError):
            await utils.invoke_payment_mcp_tool(
                "list_transactions",
                agent_id=_AGENT_ID,
                source=_SOURCE,
            )
