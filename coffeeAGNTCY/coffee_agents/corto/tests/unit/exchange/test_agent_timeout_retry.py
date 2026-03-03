# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

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


def _side_effect_for(scenario_id: str):
    from slim_bindings import SlimError

    if scenario_id == "timeout_then_success":
        return [
            SlimError.SessionError("receive timeout waiting for message"),
            _make_success_response("recovered"),
        ]
    if scenario_id == "timeout_then_timeout":
        return [SlimError.SessionError("receive timeout")] * 5
    if scenario_id == "timeout_then_non_timeout":
        return [
            SlimError.SessionError("receive timeout"),
            ConnectionError("connection refused"),
        ]
    if scenario_id == "non_timeout_no_retry":
        return [ValueError("bad request")]
    if scenario_id == "success_first_attempt":
        return [_make_success_response("first try")]
    if scenario_id == "no_payload_error":
        err = AttributeError("'NoneType' object has no attribute 'payload'")
        err.name = "payload"
        return [err]
    if scenario_id == "none_response":
        return [None]
    raise ValueError(f"Unknown scenario_id: {scenario_id}")


def _timeout_error_exception(scenario_id: str):
    if scenario_id == "session_error_in_context":
        from slim_bindings import SlimError

        e = AttributeError("missing payload")
        e.__context__ = SlimError.SessionError("receive timeout")
        return e
    if scenario_id == "plain_value_error":
        return ValueError("bad")
    raise ValueError(f"Unknown scenario_id: {scenario_id}")


def _no_payload_exception(scenario_id: str):
    if scenario_id == "no_payload_attribute":
        e = AttributeError("'NoneType' object has no attribute 'payload'")
        e.name = "payload"
        return e
    if scenario_id == "other_attribute_error":
        return AttributeError("'str' has no attribute 'foo'")
    raise ValueError(f"Unknown scenario_id: {scenario_id}")


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


_A2A_SCENARIOS = [
    pytest.param(
        "timeout_then_success",
        "recovered",
        None,
        2,
        False,
        id="timeout_then_success",
    ),
    pytest.param(
        "timeout_then_timeout",
        None,
        TransportTimeoutError,
        5,
        True,
        id="timeout_then_timeout",
    ),
    pytest.param(
        "timeout_then_non_timeout",
        None,
        ConnectionError,
        2,
        False,
        id="timeout_then_non_timeout",
    ),
    pytest.param(
        "non_timeout_no_retry",
        None,
        ValueError,
        1,
        False,
        id="non_timeout_no_retry",
    ),
    pytest.param(
        "success_first_attempt",
        "first try",
        None,
        1,
        False,
        id="success_first_attempt",
    ),
    pytest.param(
        "no_payload_error",
        None,
        RemoteAgentNoResponseError,
        1,
        False,
        id="no_payload_error",
    ),
    pytest.param(
        "none_response",
        None,
        RemoteAgentNoResponseError,
        1,
        False,
        id="none_response",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenario_id,expected_result,expected_exception,expected_await_count,check_cause",
    _A2A_SCENARIOS,
)
async def test_a2a_send_message_scenarios(
    mock_factory,
    mock_client,
    scenario_id,
    expected_result,
    expected_exception,
    expected_await_count,
    check_cause,
):
    with patch("exchange.agent.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_client.send_message = AsyncMock(side_effect=_side_effect_for(scenario_id))
        mock_factory.create_client = AsyncMock(return_value=mock_client)
        agent = ExchangeAgent(factory=mock_factory)
        if expected_exception is not None:
            with pytest.raises(expected_exception) as exc_info:
                await agent.a2a_client_send_message("test")
            if check_cause:
                assert exc_info.value.__cause__ is not None
        else:
            result = await agent.a2a_client_send_message("test")
            assert result == expected_result
        assert mock_client.send_message.await_count == expected_await_count
        if scenario_id == "timeout_then_timeout":
            assert mock_sleep.await_count == 4
            assert [mock_sleep.await_args_list[i][0][0] for i in range(4)] == [1, 3, 9, 27]


@pytest.mark.parametrize(
    "scenario_id,expected",
    [
        ("session_error_in_context", True),
        ("plain_value_error", False),
    ],
)
def test_is_timeout_error(scenario_id, expected):
    exc = _timeout_error_exception(scenario_id)
    assert _is_timeout_error(exc) is expected


@pytest.mark.parametrize(
    "scenario_id,expected",
    [
        ("no_payload_attribute", True),
        ("other_attribute_error", False),
    ],
)
def test_is_no_payload_error(scenario_id, expected):
    exc = _no_payload_exception(scenario_id)
    assert _is_no_payload_error(exc) is expected
