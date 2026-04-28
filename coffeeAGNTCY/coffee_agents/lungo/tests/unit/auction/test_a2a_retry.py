# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# _is_timeout_error and _is_no_payload_error are implementation details of a2a_retry; tested here for correctness.
from agents.supervisors.auction.graph.a2a_retry import (
    send_a2a_with_retry,
    TransportTimeoutError,
    RemoteAgentNoResponseError,
    _is_timeout_error,
    _is_no_payload_error,
)


def _make_event(text: str = "expected response"):
    """Create a simple opaque event object.  The retry wrapper doesn't inspect it."""
    event = MagicMock()
    event._text = text  # stashed so tests can assert identity
    return event


async def _async_iter(items):
    """Turn a list into an async iterator."""
    for item in items:
        yield item


async def _empty_async_iter():
    """An async iterator that yields nothing."""
    return
    yield


async def _raising_async_iter(exc):
    """An async iterator that raises on first iteration."""
    raise exc
    yield  # make it a generator


def _side_effect_for(scenario_id: str):
    try:
        from slim_bindings import SlimError
    except ImportError:
        SlimError = None
    if scenario_id == "timeout_then_success":
        if SlimError is None:
            pytest.skip("slim_bindings required for timeout scenarios")
        calls = iter([
            _raising_async_iter(SlimError.SessionError("receive timeout waiting for message")),
            _async_iter([_make_event("recovered")]),
        ])
        return lambda *a, **kw: next(calls)
    if scenario_id == "timeout_then_timeout":
        if SlimError is None:
            pytest.skip("slim_bindings required for timeout scenarios")
        return lambda *a, **kw: _raising_async_iter(SlimError.SessionError("receive timeout"))
    if scenario_id == "timeout_then_non_timeout":
        if SlimError is None:
            pytest.skip("slim_bindings required for timeout scenarios")
        calls = iter([
            _raising_async_iter(SlimError.SessionError("receive timeout")),
            _raising_async_iter(ConnectionError("connection refused")),
        ])
        return lambda *a, **kw: next(calls)
    if scenario_id == "non_timeout_no_retry":
        return lambda *a, **kw: _raising_async_iter(ValueError("bad request"))
    if scenario_id == "success_first_attempt":
        return lambda *a, **kw: _async_iter([_make_event("first try")])
    if scenario_id == "no_payload_error":
        err = AttributeError("'NoneType' object has no attribute 'payload'")
        err.name = "payload"
        return lambda *a, **kw: _raising_async_iter(err)
    if scenario_id == "none_response":
        return lambda *a, **kw: _empty_async_iter()
    if scenario_id == "no_payload_then_success":
        err = AttributeError("'NoneType' object has no attribute 'payload'")
        err.name = "payload"
        calls = iter([
            _raising_async_iter(err),
            _async_iter([_make_event("recovered")]),
        ])
        return lambda *a, **kw: next(calls)
    if scenario_id == "none_then_success":
        calls = iter([
            _empty_async_iter(),
            _async_iter([_make_event("ok")]),
        ])
        return lambda *a, **kw: next(calls)
    raise ValueError(f"Unknown scenario_id: {scenario_id}")


def _timeout_error_exception(scenario_id: str):
    if scenario_id == "session_error_in_context":
        try:
            from slim_bindings import SlimError
        except ImportError:
            pytest.skip("slim_bindings required")
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
    client = MagicMock()
    client.send_message = MagicMock()  # will be replaced per-scenario with a callable returning async iter
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
        5,
        True,
        id="no_payload_error",
    ),
    pytest.param(
        "none_response",
        None,
        RemoteAgentNoResponseError,
        5,
        False,
        id="none_response",
    ),
    pytest.param(
        "no_payload_then_success",
        "recovered",
        None,
        2,
        False,
        id="no_payload_then_success",
    ),
    pytest.param(
        "none_then_success",
        "ok",
        None,
        2,
        False,
        id="none_then_success",
    ),
]


@pytest.mark.parametrize(
    "scenario_id,expected_result,expected_exception,expected_call_count,check_cause",
    _A2A_SCENARIOS,
)
def test_send_a2a_with_retry_scenarios(
    mock_client,
    scenario_id,
    expected_result,
    expected_exception,
    expected_call_count,
    check_cause,
):
    message = MagicMock()
    with patch("agents.supervisors.auction.graph.a2a_retry.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_client.send_message = MagicMock(side_effect=_side_effect_for(scenario_id))

        async def run():
            return await send_a2a_with_retry(mock_client, message)

        if expected_exception is not None:
            with pytest.raises(expected_exception) as exc_info:
                asyncio.run(run())
            if check_cause:
                assert exc_info.value.__cause__ is not None
        else:
            result = asyncio.run(run())
            # Result is now a list of opaque events; check the stashed marker.
            assert isinstance(result, list)
            assert len(result) > 0
            assert result[0]._text == expected_result
        assert mock_client.send_message.call_count == expected_call_count
        if expected_call_count == 5:
            assert mock_sleep.await_count == 4
            assert [mock_sleep.await_args_list[i][0][0] for i in range(4)] == [1, 3, 9, 27]
        elif expected_call_count == 2 and expected_exception is None:
            assert mock_sleep.await_count == 1
            assert mock_sleep.await_args[0][0] == 1


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

