# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agents.supervisors.auction.graph.a2a_retry import TransportTimeoutError

from tests.integration._auction_helpers import TRANSPORT_MATRIX, response_has_inventory_amount


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


@pytest.mark.no_pin_auction_shared
@pytest.mark.parametrize(
    "transport_config",
    [TRANSPORT_MATRIX[0]],
    indirect=True,
)
def test_auction_a2a_timeout_returns_user_visible_error(auction_supervisor_client):
    """When send_a2a_with_retry raises TransportTimeoutError, graph returns 200 with error message in body.

    Stub a2a_client_factory.create so execution reaches send_a2a_with_retry: without it, SLIM/agent-card
    handshake can fail before A2A send (mock would never be called).
    """
    with patch(
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
