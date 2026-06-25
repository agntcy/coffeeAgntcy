# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from a2a.types import Message, Part, Role, TextPart
from exchange.errors import (
    RemoteAgentNoResponseError,
    TransportTimeoutError,
    _is_no_payload_error,
    _is_timeout_error,
)


def _make_success_response(text: str = "expected response") -> Message:
    """Real Message so _extract_text_from_events() accepts the mock response."""
    return Message(
        messageId=str(uuid4()),
        role=Role.user,
        parts=[Part(root=TextPart(text=text))],
    )


async def _async_iter(items):
    for item in items:
        yield item


async def _empty_async_iter():
    return
    yield


async def _raising_async_iter(exc):
    raise exc
    yield


def _side_effect_for(scenario_id: str):
    from slim_bindings import SlimError

    if scenario_id == "timeout_then_success":
        calls = iter(
            [
                _raising_async_iter(
                    SlimError.SessionError("receive timeout waiting for message")
                ),
                _async_iter([_make_success_response("recovered")]),
            ]
        )
        return lambda *a, **kw: next(calls)
    if scenario_id == "timeout_then_timeout":
        return lambda *a, **kw: _raising_async_iter(
            SlimError.SessionError("receive timeout")
        )
    if scenario_id == "timeout_then_non_timeout":
        calls = iter(
            [
                _raising_async_iter(SlimError.SessionError("receive timeout")),
                _raising_async_iter(ConnectionError("connection refused")),
            ]
        )
        return lambda *a, **kw: next(calls)
    if scenario_id == "non_timeout_no_retry":
        return lambda *a, **kw: _raising_async_iter(ValueError("bad request"))
    if scenario_id == "success_first_attempt":
        return lambda *a, **kw: _async_iter([_make_success_response("first try")])
    if scenario_id == "no_payload_error":
        err = AttributeError("'NoneType' object has no attribute 'payload'")
        err.name = "payload"
        return lambda *a, **kw: _raising_async_iter(err)
    if scenario_id == "none_response":
        return lambda *a, **kw: _empty_async_iter()
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
def mock_client():
    return MagicMock()


_A2A_SCENARIOS = [
    pytest.param(
        "timeout_then_success", "recovered", None, 2, False, id="timeout_then_success"
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
        "non_timeout_no_retry", None, ValueError, 1, False, id="non_timeout_no_retry"
    ),
    pytest.param(
        "success_first_attempt", "first try", None, 1, False, id="success_first_attempt"
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
        "none_response", None, RemoteAgentNoResponseError, 1, False, id="none_response"
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenario_id,expected_result,expected_exception,expected_call_count,check_cause",
    _A2A_SCENARIOS,
)
async def test_a2a_send_message_scenarios(
    mock_client,
    scenario_id,
    expected_result,
    expected_exception,
    expected_call_count,
    check_cause,
):
    import exchange.agent as agent_module  # Note: required here, because of module reloads for integration tests.
    import exchange.errors as exchange_errors  # Note: required here, because of module reloads for integration tests.

    mock_client.send_message = MagicMock(side_effect=_side_effect_for(scenario_id))
    with (
        patch.object(
            agent_module.asyncio, "sleep", new_callable=AsyncMock
        ) as mock_sleep,
        patch.object(
            agent_module.a2a_client_factory,
            "create",
            new_callable=AsyncMock,
            return_value=mock_client,
        ),
    ):
        agent = agent_module.ExchangeAgent()
        if expected_exception is not None:
            if getattr(expected_exception, "__module__", "") == "exchange.errors":
                exc_type = getattr(exchange_errors, expected_exception.__name__)
            else:
                exc_type = expected_exception
            with pytest.raises(exc_type) as exc_info:
                await agent.a2a_client_send_message("test")
            if check_cause:
                assert exc_info.value.__cause__ is not None
        else:
            result = await agent.a2a_client_send_message("test")
            assert result == expected_result

        assert mock_client.send_message.call_count == expected_call_count
        if scenario_id == "timeout_then_timeout":
            assert mock_sleep.await_count == 4
            assert [mock_sleep.await_args_list[i][0][0] for i in range(4)] == [
                1,
                3,
                9,
                27,
            ]
        elif scenario_id == "timeout_then_success":
            assert mock_sleep.await_count == 1
            assert mock_sleep.await_args[0][0] == 1


@pytest.mark.parametrize(
    "scenario_id,expected",
    [("session_error_in_context", True), ("plain_value_error", False)],
)
def test_is_timeout_error(scenario_id, expected):
    assert _is_timeout_error(_timeout_error_exception(scenario_id)) is expected


@pytest.mark.parametrize(
    "scenario_id,expected",
    [("no_payload_attribute", True), ("other_attribute_error", False)],
)
def test_is_no_payload_error(scenario_id, expected):
    assert _is_no_payload_error(_no_payload_exception(scenario_id)) is expected
