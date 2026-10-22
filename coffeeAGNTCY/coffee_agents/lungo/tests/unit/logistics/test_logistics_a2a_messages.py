# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the logistics agents' a2a-sdk 1.x message handling.

Covers the executors' message-mode replies and the supervisor's parsing of
group chat replies built from real protobuf responses.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from a2a.types import (
    Message,
    Part,
    Role,
    SendMessageResponse,
    StreamResponse,
    Task,
    TaskState,
    TaskStatus,
)
from a2a.utils.errors import (
    ContentTypeNotSupportedError,
    InternalError,
    UnsupportedOperationError,
)

from agents.supervisors.logistics.graph import tools

_ORDER_ID = "0f6b2a6e-1c1d-4c5e-9a43-2d7c1a9e8b11"

EXECUTORS = [
    pytest.param(
        "agents.logistics.shipper.agent_executor",
        "ShipperAgentExecutor",
        "agents.logistics.shipper.card",
        id="shipper",
    ),
    pytest.param(
        "agents.logistics.accountant.agent_executor",
        "AccountantAgentExecutor",
        "agents.logistics.accountant.card",
        id="accountant",
    ),
    pytest.param(
        "agents.logistics.farm.agent_executor",
        "FarmAgentExecutor",
        "agents.logistics.farm.card",
        id="farm",
    ),
]


def _executor(module_name: str, class_name: str, *, output="SHIPPED | ok"):
    """Build an executor without its LLM-backed agent."""
    cls = getattr(importlib.import_module(module_name), class_name)
    executor = cls.__new__(cls)
    executor.agent = SimpleNamespace(ainvoke=AsyncMock(return_value=output))
    return executor


def _context(text: str | None = "create an order"):
    parts = [Part(text=text)] if text is not None else []
    message = Message(message_id="in-1", role=Role.ROLE_USER, parts=parts)
    return SimpleNamespace(message=message, get_user_input=lambda: text or "")


def _queue():
    queue = MagicMock()
    queue.enqueue_event = AsyncMock()
    return queue


# ---------------------------------------------------------------------------
# Executors: message mode
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module_name,class_name,card_module", EXECUTORS)
async def test_executor_replies_with_one_message_and_no_task(
    module_name, class_name, card_module
):
    executor = _executor(module_name, class_name)
    queue = _queue()

    await executor.execute(_context(), queue)

    [call] = queue.enqueue_event.await_args_list
    (event,) = call.args
    assert isinstance(event, Message)
    assert not isinstance(event, Task)
    assert event.role == Role.ROLE_AGENT
    assert [p.text for p in event.parts] == ["SHIPPED | ok"]
    card = importlib.import_module(card_module).AGENT_CARD
    assert dict(event.metadata) == {"name": card.name}


@pytest.mark.parametrize("module_name,class_name,card_module", EXECUTORS)
async def test_executor_rejects_a_message_without_parts(
    module_name, class_name, card_module
):
    executor = _executor(module_name, class_name)
    queue = _queue()

    with pytest.raises(ContentTypeNotSupportedError):
        await executor.execute(_context(text=None), queue)
    queue.enqueue_event.assert_not_awaited()


@pytest.mark.parametrize("module_name,class_name,card_module", EXECUTORS)
async def test_executor_wraps_agent_failures(module_name, class_name, card_module):
    executor = _executor(module_name, class_name)
    executor.agent.ainvoke.side_effect = RuntimeError("llm down")

    with pytest.raises(InternalError) as excinfo:
        await executor.execute(_context(), _queue())
    assert isinstance(excinfo.value.__cause__, RuntimeError)


@pytest.mark.parametrize("module_name,class_name,card_module", EXECUTORS)
async def test_executor_cancel_is_unsupported(module_name, class_name, card_module):
    executor = _executor(module_name, class_name)

    with pytest.raises(UnsupportedOperationError):
        await executor.cancel(_context(), _queue())


# ---------------------------------------------------------------------------
# Supervisor: group chat reply parsing
# ---------------------------------------------------------------------------


def _reply(text: str, name: str | None, *, streaming: bool = False):
    metadata = {"name": name} if name is not None else None
    message = Message(
        message_id="r1",
        role=Role.ROLE_AGENT,
        parts=[Part(text=text)],
        metadata=metadata,
    )
    if streaming:
        return StreamResponse(message=message)
    return SendMessageResponse(message=message)


def test_order_request_is_a_user_message():
    request = tools._order_request("hello")
    assert request.message.role == Role.ROLE_USER
    assert [p.text for p in request.message.parts] == ["hello"]
    assert request.message.message_id


@pytest.mark.parametrize("streaming", [False, True], ids=["send", "stream"])
@pytest.mark.parametrize(
    "name,expected_sender",
    [
        ("Shipping agent", "Shipper"),
        ("Shipper agent", "Shipper"),
        ("Tatooine Farm agent", "Tatooine Farm"),
        ("Accountant agent", "Accountant"),
        (None, "Unknown"),
    ],
)
def test_parse_order_event_reads_metadata_name_and_text(
    streaming, name, expected_sender
):
    response = _reply(
        f"HANDOVER_TO_SHIPPER | Tatooine Farm -> Shipper: order {_ORDER_ID} ready",
        name,
        streaming=streaming,
    )

    event = tools._parse_order_event(response)

    assert event is not None
    assert event["sender"] == expected_sender
    assert event["state"] == "HANDOVER_TO_SHIPPER"
    assert event["receiver"] == "Shipper"
    assert event["message"] == f"order {_ORDER_ID} ready"
    assert event["order_id"] == _ORDER_ID


@pytest.mark.parametrize(
    "response",
    [
        pytest.param(_reply("no pipe separator here", "Shipping agent"), id="no_pipe"),
        pytest.param(_reply("STATE | no arrow", "Shipping agent"), id="no_arrow"),
        pytest.param(_reply("", "Shipping agent"), id="empty_text"),
        pytest.param(
            StreamResponse(
                task=Task(
                    id="t",
                    context_id="c",
                    status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
                )
            ),
            id="task_without_message",
        ),
    ],
)
def test_parse_order_event_returns_none_for_unparseable_replies(response):
    assert tools._parse_order_event(response) is None


def test_summarize_a2a_responses_groups_by_agent_and_marks_final():
    responses = [
        _reply("RECEIVED_ORDER", "Tatooine Farm agent"),
        _reply("I am idle", "Accountant agent"),
        _reply("HANDOVER_TO_SHIPPER", "Tatooine Farm agent"),
        _reply("HANDOVER_TO_SHIPPER", "Tatooine Farm agent"),
        _reply("PAYMENT_COMPLETE", "Accountant agent"),
        _reply("Order delivered", "Shipping agent"),
        SendMessageResponse(),
    ]

    summary = tools._summarize_a2a_responses(responses)

    assert summary == (
        "Order status updates: "
        "Tatooine Farm agent: RECEIVED_ORDER, HANDOVER_TO_SHIPPER | "
        "Accountant agent: PAYMENT_COMPLETE | "
        "Shipping agent: Order delivered (final)"
    )


def test_summarize_a2a_responses_with_only_idle_replies():
    responses = [_reply("idle", "Shipping agent"), _reply("IDLE now", None)]
    assert (
        tools._summarize_a2a_responses(responses)
        == "No non-idle status updates received."
    )
