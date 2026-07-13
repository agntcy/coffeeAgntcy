# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.mcp_servers.utils.invoke_payment_mcp_tool.

The payment helper is now a thin wrapper over the shared
``common.mcp_client.call_mcp_tool`` primitive. These tests guard the
payment-specific behavior: the identity-auth gate, delegation with the correct
payment arguments, and mapping auth failures to ``AuthError``. The shared MCP
client contract itself is covered in tests/unit/common/test_mcp_client.py.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from agents.exceptions import AuthError
from agents.mcp_servers import utils

_AGENT_ID = "Colombia Coffee Farm"
_SOURCE = "colombia_coffee_farm"


@pytest.fixture
def identity_auth_on(monkeypatch):
    monkeypatch.setenv("IDENTITY_AUTH_ENABLED", "true")


async def test_returns_empty_when_identity_auth_disabled(monkeypatch):
    monkeypatch.delenv("IDENTITY_AUTH_ENABLED", raising=False)

    with patch.object(utils, "call_mcp_tool") as call_mcp_tool:
        result = await utils.invoke_payment_mcp_tool(
            "create_payment",
            agent_id=_AGENT_ID,
            source=_SOURCE,
        )

    assert result == {}
    call_mcp_tool.assert_not_called()


async def test_delegates_to_call_mcp_tool_with_payment_args(identity_auth_on):
    captured = {}
    expected = {"ok": True, "status": "payment created"}

    async def fake_call_mcp_tool(**kwargs):
        captured.update(kwargs)
        return expected

    with patch.object(utils, "call_mcp_tool", side_effect=fake_call_mcp_tool):
        result = await utils.invoke_payment_mcp_tool(
            "create_payment",
            agent_id=_AGENT_ID,
            source=_SOURCE,
            workflow_name="Test Workflow Alpha",
            instance_id="instance://00000000-0000-4000-8000-000000000001",
        )

    assert result == expected
    assert captured["topic"] == "lungo_payment_service"
    assert captured["tool_name"] == "create_payment"
    assert captured["agent_id"] == _AGENT_ID
    assert captured["source"] == _SOURCE
    assert captured["workflow_name"] == "Test Workflow Alpha"
    assert captured["instance_id"] == "instance://00000000-0000-4000-8000-000000000001"
    # Payment-specific transport config preserved through consolidation.
    assert captured["use_shared_secret"] is False
    assert captured["transport_name"] == "default/default/fast_mcp_client"


@pytest.mark.parametrize(
    "tool_name, expected_fragment",
    [
        ("create_payment", "creating a payment"),
        ("list_transactions", "listing transactions"),
    ],
)
async def test_authentication_failure_is_wrapped_as_auth_error(
    identity_auth_on, tool_name, expected_fragment
):
    async def unauthorized(**kwargs):
        raise RuntimeError("Authentication failed for the payment service")

    with patch.object(utils, "call_mcp_tool", side_effect=unauthorized):
        with pytest.raises(AuthError) as exc_info:
            await utils.invoke_payment_mcp_tool(
                tool_name,
                agent_id=_AGENT_ID,
                source=_SOURCE,
            )

    assert expected_fragment in str(exc_info.value)


async def test_non_auth_error_propagates_unchanged(identity_auth_on):
    async def boom(**kwargs):
        raise RuntimeError("transport exploded")

    with patch.object(utils, "call_mcp_tool", side_effect=boom):
        with pytest.raises(RuntimeError, match="transport exploded"):
            await utils.invoke_payment_mcp_tool(
                "create_payment",
                agent_id=_AGENT_ID,
                source=_SOURCE,
            )
