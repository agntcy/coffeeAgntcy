# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import inspect

import pytest
from agntcy_app_sdk.transport.slim.transport import SLIMTransport
from common.slim_request_timeout import apply_slim_request_timeout


@pytest.fixture(autouse=True)
def restore_request():
    original = SLIMTransport.request
    yield
    SLIMTransport.request = original


@pytest.fixture
def recorded_calls(monkeypatch):
    """Replace the SDK method with a recorder that keeps the real signature."""
    calls = []

    async def request(self, recipient, message, timeout: int = 6, **kwargs):
        calls.append(timeout)
        return "reply"

    monkeypatch.setattr(SLIMTransport, "request", request, raising=True)
    return calls


async def test_applies_timeout_when_caller_omits_it(recorded_calls):
    apply_slim_request_timeout(20)

    assert await SLIMTransport.request(None, "topic", "message") == "reply"
    assert recorded_calls == [20]


@pytest.mark.parametrize("call_style", ["keyword", "positional"])
async def test_caller_supplied_timeout_wins(recorded_calls, call_style):
    apply_slim_request_timeout(20)

    if call_style == "keyword":
        await SLIMTransport.request(None, "topic", "message", timeout=5)
    else:
        await SLIMTransport.request(None, "topic", "message", 5)

    assert recorded_calls == [5]


async def test_reapplying_does_not_stack_wrappers(recorded_calls):
    apply_slim_request_timeout(20)
    wrapped_once = SLIMTransport.request

    apply_slim_request_timeout(20)
    assert SLIMTransport.request is wrapped_once

    apply_slim_request_timeout(30)
    assert inspect.unwrap(SLIMTransport.request) is inspect.unwrap(wrapped_once)

    await SLIMTransport.request(None, "topic", "message")
    assert recorded_calls == [30]


async def test_skipped_when_sdk_drops_the_parameter(monkeypatch, caplog):
    async def request(self, recipient, message, **kwargs):
        return kwargs

    monkeypatch.setattr(SLIMTransport, "request", request, raising=True)

    apply_slim_request_timeout(20)

    assert SLIMTransport.request is request
    assert await SLIMTransport.request(None, "topic", "message") == {}


@pytest.mark.parametrize("timeout", [0, -1])
def test_rejects_non_positive_timeout(timeout):
    with pytest.raises(ValueError):
        apply_slim_request_timeout(timeout)
