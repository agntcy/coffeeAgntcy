# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Integration test: when the agent raises TransportTimeoutError, the API returns 504."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.parametrize(
    "transport_config",
    [{"DEFAULT_MESSAGE_TRANSPORT": "SLIM", "TRANSPORT_SERVER_ENDPOINT": "http://127.0.0.1:46357"}],
    indirect=True,
)
def test_timeout_returns_504(supervisor_client, transport_config):
    import exchange.main as exchange_main
    from exchange.errors import TransportTimeoutError

    with patch.object(exchange_main, "exchange_agent", MagicMock()) as mock_agent:
        mock_agent.execute_agent_with_llm = AsyncMock(
            side_effect=TransportTimeoutError("timeout", cause=None)
        )
        resp = supervisor_client.post("/agent/prompt", json={"prompt": "test"})
    assert resp.status_code == 504
    data = resp.json()
    assert "detail" in data
    detail = data["detail"]
    assert isinstance(detail, str)
    assert "timeout" in detail.lower() or "did not respond" in detail.lower()

