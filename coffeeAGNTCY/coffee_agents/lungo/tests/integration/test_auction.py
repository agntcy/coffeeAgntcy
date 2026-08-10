# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agents.supervisors.auction.graph.a2a_retry import TransportTimeoutError
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable

from tests.integration._auction_helpers import TRANSPORT_MATRIX, response_has_inventory_amount


class _FakeStructuredRunnable(Runnable):
    """Stand-in for ``get_llm(...).with_structured_output(...)`` returning a fixed value."""

    def __init__(self, value):
        self._value = value

    def invoke(self, input, config=None, **kwargs):
        return self._value

    async def ainvoke(self, input, config=None, **kwargs):
        return self._value


class _FakeRoutingLLM(Runnable):
    """Minimal ``get_llm()`` replacement so tests need no real LLM provider.

    - Used as a pipe target (``prompt | llm``) it returns a fixed routing ``AIMessage``.
    - ``.with_structured_output(schema, ...)`` yields a runnable returning
      ``schema(should_continue=False, ...)`` so the reflection node routes to END.
    """

    def __init__(self, route: str):
        self._route = route

    def invoke(self, input, config=None, **kwargs):
        return AIMessage(content=self._route)

    async def ainvoke(self, input, config=None, **kwargs):
        return AIMessage(content=self._route)

    def with_structured_output(self, schema, **kwargs):
        return _FakeStructuredRunnable(
            schema(should_continue=False, reason="stubbed: no real LLM in this test"),
        )


@pytest.mark.parametrize(
    "transport_config",
    [TRANSPORT_MATRIX[0]],
    indirect=True,
)
def test_auction_suggested_prompts_streaming_matches_default(auction_supervisor_client):
    default_resp = auction_supervisor_client.get("/suggested-prompts")
    streaming_resp = auction_supervisor_client.get(
        "/suggested-prompts", params={"pattern": "streaming"}
    )
    assert default_resp.status_code == 200
    assert streaming_resp.status_code == 200
    assert default_resp.json() == streaming_resp.json()


@pytest.mark.parametrize(
    "transport_config",
    [TRANSPORT_MATRIX[0]],
    indirect=True,
)
def test_auction_a2a_timeout_returns_user_visible_error(auction_supervisor_client):
    """When send_a2a_with_retry raises TransportTimeoutError, graph returns 200 with error message in body.

    Stub a2a_client_factory.create so execution reaches send_a2a_with_retry: without it, SLIM/agent-card
    handshake can fail before A2A send (mock would never be called).

    Stub get_llm too: the supervisor routing node and the reflection node call the LLM, which would
    otherwise require LLM provider secrets/config (unavailable in the CI tier and when no .env exists).
    The fake routes to the single-farm branch and ends the reflection loop, so the test exercises only
    the transport-error handling it is meant to cover, with no real LLM.
    """
    with patch(
        "agents.supervisors.auction.graph.graph.get_llm",
        return_value=_FakeRoutingLLM("inventory_single_farm"),
    ), patch(
        "agents.supervisors.auction.graph.tools.a2a_client_factory.create",
        new_callable=AsyncMock,
        return_value=MagicMock(),
    ), patch(
        "agents.supervisors.auction.graph.tools.send_a2a_with_retry",
        new_callable=AsyncMock,
        side_effect=TransportTimeoutError("timeout", cause=None),
    ) as mock_send_a2a:
        resp = auction_supervisor_client.post(
            "/agent/prompt",
            json={"prompt": "What is the inventory of coffee in Brazil?"},
        )
        assert mock_send_a2a.called
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert not response_has_inventory_amount(data["response"]), "Expected error response, not inventory success"
    assert data["response"] == "I encountered an issue retrieving information from the Brazil farm. Please try again later."
