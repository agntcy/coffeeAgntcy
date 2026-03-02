# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import AsyncMock, MagicMock

from exchange.agent import ExchangeAgent
from exchange.errors import (
    TransportTimeoutError,
    RemoteAgentNoResponseError,
    _is_timeout_error,
    _is_no_payload_error,
)


def _make_success_response(text: str = "expected response"):
    part = MagicMock()
    part.text = text
    parts = [MagicMock()]
    parts[0].root = part
    result = MagicMock()
    result.parts = parts
    root = MagicMock()
    root.result = result
    root.error = None
    response = MagicMock()
    response.root = root
    return response


@pytest.fixture
def mock_factory():
    factory = MagicMock()
    factory.create_transport.return_value = MagicMock()
    return factory


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.send_message = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_timeout_then_success(mock_factory, mock_client):
    from slim_bindings import SlimError

    mock_client.send_message = AsyncMock(
        side_effect=[
            SlimError.SessionError("receive timeout waiting for message"),
            _make_success_response("recovered"),
        ]
    )
    mock_factory.create_client = AsyncMock(return_value=mock_client)
    agent = ExchangeAgent(factory=mock_factory)
    result = await agent.a2a_client_send_message("test")
    assert result == "recovered"
    assert mock_client.send_message.await_count == 2


@pytest.mark.asyncio
async def test_timeout_then_timeout(mock_factory, mock_client):
    from slim_bindings import SlimError

    mock_client.send_message = AsyncMock(
        side_effect=[
            SlimError.SessionError("receive timeout"),
            SlimError.SessionError("receive timeout"),
        ]
    )
    mock_factory.create_client = AsyncMock(return_value=mock_client)
    agent = ExchangeAgent(factory=mock_factory)
    with pytest.raises(TransportTimeoutError) as exc_info:
        await agent.a2a_client_send_message("test")
    assert exc_info.value.__cause__ is not None
    assert mock_client.send_message.await_count == 2


@pytest.mark.asyncio
async def test_timeout_then_non_timeout_error(mock_factory, mock_client):
    from slim_bindings import SlimError

    mock_client.send_message = AsyncMock(
        side_effect=[
            SlimError.SessionError("receive timeout"),
            ConnectionError("connection refused"),
        ]
    )
    mock_factory.create_client = AsyncMock(return_value=mock_client)
    agent = ExchangeAgent(factory=mock_factory)
    with pytest.raises(ConnectionError):
        await agent.a2a_client_send_message("test")
    assert mock_client.send_message.await_count == 2


@pytest.mark.asyncio
async def test_non_timeout_on_first_attempt_no_retry(mock_factory, mock_client):
    mock_client.send_message = AsyncMock(side_effect=ValueError("bad request"))
    mock_factory.create_client = AsyncMock(return_value=mock_client)
    agent = ExchangeAgent(factory=mock_factory)
    with pytest.raises(ValueError):
        await agent.a2a_client_send_message("test")
    assert mock_client.send_message.await_count == 1


@pytest.mark.asyncio
async def test_success_on_first_attempt(mock_factory, mock_client):
    mock_client.send_message = AsyncMock(return_value=_make_success_response("first try"))
    mock_factory.create_client = AsyncMock(return_value=mock_client)
    agent = ExchangeAgent(factory=mock_factory)
    result = await agent.a2a_client_send_message("test")
    assert result == "first try"
    assert mock_client.send_message.await_count == 1


@pytest.mark.asyncio
async def test_no_payload_error_no_timeout_in_chain_no_retry(mock_factory, mock_client):
    err = AttributeError("'NoneType' object has no attribute 'payload'")
    err.name = "payload"
    assert not _is_timeout_error(err)
    mock_client.send_message = AsyncMock(side_effect=err)
    mock_factory.create_client = AsyncMock(return_value=mock_client)
    agent = ExchangeAgent(factory=mock_factory)
    with pytest.raises(RemoteAgentNoResponseError):
        await agent.a2a_client_send_message("test")
    assert mock_client.send_message.await_count == 1


@pytest.mark.asyncio
async def test_defensive_check_none_response(mock_factory, mock_client):
    mock_client.send_message = AsyncMock(return_value=None)
    mock_factory.create_client = AsyncMock(return_value=mock_client)
    agent = ExchangeAgent(factory=mock_factory)
    with pytest.raises(RemoteAgentNoResponseError):
        await agent.a2a_client_send_message("test")
    assert mock_client.send_message.await_count == 1


def test_is_timeout_error_true_when_session_error_in_context():
    from slim_bindings import SlimError

    e = AttributeError("missing payload")
    e.__context__ = SlimError.SessionError("receive timeout")
    assert _is_timeout_error(e) is True


def test_is_timeout_error_false_for_plain_value_error():
    assert _is_timeout_error(ValueError("bad")) is False


def test_is_no_payload_error_true():
    e = AttributeError("'NoneType' object has no attribute 'payload'")
    e.name = "payload"
    assert _is_no_payload_error(e) is True


def test_is_no_payload_error_false_for_other_attribute_error():
    assert _is_no_payload_error(AttributeError("'str' has no attribute 'foo'")) is False

