# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the auction supervisor's farm broadcasts.

A partial broadcast (a farm failed or never replied) arrives from the app SDK
as ``A2ABroadcastError``; the successful replies must still reach the user,
together with a note on the farms that did not answer.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from a2a.types import (
    Message,
    Part,
    Role,
    SendMessageRequest,
    SendMessageResponse,
    StreamResponse,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from agntcy_app_sdk import get_agent_identifier
from agntcy_app_sdk.semantic.a2a import (
    A2ABroadcastError,
    A2ABroadcastTimeoutError,
    BroadcastFailure,
)

from agents.supervisors.auction.graph import tools
from agents.supervisors.auction.graph.shared import farm_registry

COLOMBIA = "Colombia Coffee Farm"
VIETNAM = "Vietnam Coffee Farm"


def _identifier(slug: str) -> str:
    """The sender identity a farm stamps on its replies (its topic)."""
    return get_agent_identifier(farm_registry.get(slug))


def _farm_message(name: str, text: str) -> Message:
    return Message(
        message_id=f"reply-{name}",
        role=Role.ROLE_AGENT,
        parts=[Part(text=text)],
        metadata={"name": name},
    )


def _install_client(monkeypatch, **methods):
    """Make ``a2a_client_factory.create`` return a client with ``methods``."""
    client = SimpleNamespace(**methods)
    create = AsyncMock(return_value=client)
    monkeypatch.setattr(tools, "a2a_client_factory", SimpleNamespace(create=create))
    return create


async def _collect(agen) -> list[str]:
    return [chunk async for chunk in agen]


# ---------------------------------------------------------------------------
# Non-streaming broadcast
# ---------------------------------------------------------------------------


async def test_broadcast_returns_every_reply(monkeypatch):
    sent: list = []

    async def broadcast_message(request, *, recipients, context):
        sent.append((request, recipients))
        return [
            SendMessageResponse(message=_farm_message("Brazil Coffee Farm", "100 lb")),
            SendMessageResponse(message=_farm_message("Vietnam Coffee Farm", "50 lb")),
        ]

    create = _install_client(monkeypatch, broadcast_message=broadcast_message)

    result = await tools.get_all_farms_yield_inventory("how much coffee?")

    assert result == "Brazil Coffee Farm : 100 lb\nVietnam Coffee Farm : 50 lb"
    [(request, recipients)] = sent
    assert isinstance(request, SendMessageRequest)
    assert request.message.parts[0].text == "how much coffee?"
    assert len(recipients) == 3
    assert create.await_args.kwargs == {"interceptors": [tools._event_interceptor]}


async def test_broadcast_keeps_partial_replies_and_reports_each_farm_once(
    monkeypatch,
):
    async def broadcast_message(request, *, recipients, context):
        raise A2ABroadcastError(
            responses=[
                SendMessageResponse(
                    message=_farm_message("Brazil Coffee Farm", "100 lb")
                )
            ],
            failures=[
                BroadcastFailure(
                    sender=_identifier("colombia"),
                    error=RuntimeError("weather service down"),
                )
            ],
            missing_recipients=[_identifier("vietnam")],
            expected=3,
            received=2,
        )

    _install_client(monkeypatch, broadcast_message=broadcast_message)

    result = await tools.get_all_farms_yield_inventory("how much coffee?")

    assert result.splitlines() == [
        "Brazil Coffee Farm : 100 lb",
        "Incomplete answer: 2 of 3 farms gave no usable reply: "
        f"{COLOMBIA} returned an error (weather service down); "
        f"{VIETNAM} did not reply at all.",
    ]
    assert result.count(COLOMBIA) == 1


async def test_broadcast_names_unreplied_farms_when_the_sdk_cannot(monkeypatch):
    # no missing_recipients: the SDK could not tell who stayed silent
    async def broadcast_message(request, *, recipients, context):
        raise A2ABroadcastError(
            responses=[
                SendMessageResponse(
                    message=_farm_message("Brazil Coffee Farm", "100 lb")
                )
            ],
            failures=[
                BroadcastFailure(
                    sender=_identifier("colombia"), error=RuntimeError("boom")
                )
            ],
            expected=3,
            received=2,
        )

    _install_client(monkeypatch, broadcast_message=broadcast_message)

    result = await tools.get_all_farms_yield_inventory("how much coffee?")

    assert result.splitlines()[1] == (
        "Incomplete answer: 2 of 3 farms gave no usable reply: "
        f"{COLOMBIA} returned an error (boom); {VIETNAM} did not reply at all."
    )


async def test_broadcast_failure_without_sender_is_listed_once(monkeypatch):
    async def broadcast_message(request, *, recipients, context):
        raise A2ABroadcastError(
            responses=[
                SendMessageResponse(
                    message=_farm_message("Brazil Coffee Farm", "100 lb")
                ),
                SendMessageResponse(message=_farm_message(VIETNAM, "50 lb")),
            ],
            failures=[BroadcastFailure(sender=None, error=RuntimeError("boom"))],
            expected=3,
            received=3,
        )

    _install_client(monkeypatch, broadcast_message=broadcast_message)

    result = await tools.get_all_farms_yield_inventory("how much coffee?")

    assert result.splitlines()[-1] == (
        f"Incomplete answer: 1 of 3 farms gave no usable reply: {COLOMBIA} gave no "
        "usable reply. Errors reported: boom."
    )


async def test_broadcast_timeout_with_partial_replies_says_in_time(monkeypatch):
    async def broadcast_message(request, *, recipients, context):
        raise A2ABroadcastTimeoutError(
            responses=[
                SendMessageResponse(
                    message=_farm_message("Brazil Coffee Farm", "100 lb")
                )
            ],
            missing_recipients=[_identifier("colombia"), _identifier("vietnam")],
            expected=3,
            received=1,
            timed_out=True,
        )

    _install_client(monkeypatch, broadcast_message=broadcast_message)

    result = await tools.get_all_farms_yield_inventory("how much coffee?")

    assert result.splitlines()[1] == (
        "Incomplete answer: 2 of 3 farms gave no usable reply: "
        f"{COLOMBIA} did not reply in time; {VIETNAM} did not reply in time."
    )


async def test_broadcast_with_no_replies_fails(monkeypatch):
    async def broadcast_message(request, *, recipients, context):
        raise A2ABroadcastTimeoutError(expected=3, received=0, timed_out=True)

    _install_client(monkeypatch, broadcast_message=broadcast_message)

    with pytest.raises(
        tools.A2AAgentError,
        match="Failed to communicate.*Incomplete answer: 3 of 3 farms",
    ):
        await tools.get_all_farms_yield_inventory("how much coffee?")


def _empty_reply(name: str) -> SendMessageResponse:
    """A reply without usable text (what a farm sends when it has nothing to say)."""
    return SendMessageResponse(message=_farm_message(name, ""))


async def test_broadcast_skips_an_unusable_reply_and_keeps_the_others(monkeypatch):
    async def broadcast_message(request, *, recipients, context):
        return [
            SendMessageResponse(message=_farm_message("Brazil Coffee Farm", "100 lb")),
            _empty_reply(VIETNAM),
            SendMessageResponse(message=_farm_message(COLOMBIA, "70 lb")),
        ]

    _install_client(monkeypatch, broadcast_message=broadcast_message)

    result = await tools.get_all_farms_yield_inventory("how much coffee?")

    assert result.splitlines() == [
        "Brazil Coffee Farm : 100 lb",
        f"{COLOMBIA} : 70 lb",
        "Incomplete answer: 1 of 3 farms gave no usable reply: "
        f"{VIETNAM} gave no usable reply.",
    ]


async def test_broadcast_with_only_unusable_replies_fails(monkeypatch):
    async def broadcast_message(request, *, recipients, context):
        return [_empty_reply(VIETNAM)]

    _install_client(monkeypatch, broadcast_message=broadcast_message)

    with pytest.raises(
        tools.A2AAgentError,
        match="Failed to communicate.*Incomplete answer: 3 of 3 farms",
    ):
        await tools.get_all_farms_yield_inventory("how much coffee?")


def test_incomplete_note_does_not_name_a_farm_that_already_replied():
    error = A2ABroadcastError(
        missing_recipients=[_identifier("vietnam")], expected=3, received=2
    )

    # the SDK lists Vietnam as missing although its reply was usable
    assert (
        tools._incomplete_broadcast_note(
            {"Brazil Coffee Farm", COLOMBIA, VIETNAM}, error
        )
        is None
    )

    note = tools._incomplete_broadcast_note({"Brazil Coffee Farm", VIETNAM}, error)
    assert note is not None
    assert VIETNAM not in note
    assert note.count(COLOMBIA) == 1


def test_incomplete_note_keeps_an_empty_reply_over_missing_but_not_over_an_error():
    error = A2ABroadcastError(
        failures=[
            BroadcastFailure(sender=_identifier("colombia"), error=RuntimeError("boom"))
        ],
        missing_recipients=[_identifier("vietnam")],
        expected=3,
        received=1,
    )

    note = tools._incomplete_broadcast_note(
        {"Brazil Coffee Farm"}, error, {VIETNAM, COLOMBIA}
    )

    assert note is not None
    assert f"{VIETNAM} gave no usable reply" in note
    assert f"{COLOMBIA} returned an error (boom)" in note
    assert "did not reply" not in note


# ---------------------------------------------------------------------------
# Streaming broadcast
# ---------------------------------------------------------------------------


async def test_streaming_broadcast_skips_progress_and_reports_failures(monkeypatch):
    async def broadcast_message_streaming(request, *, recipients, context):
        yield StreamResponse(
            status_update=TaskStatusUpdateEvent(
                task_id="t",
                context_id="c",
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
            )
        )
        yield StreamResponse(message=_farm_message("Brazil Coffee Farm", "100 lb"))
        raise A2ABroadcastError(
            failures=[
                BroadcastFailure(
                    sender=_identifier("colombia"), error=RuntimeError("boom")
                )
            ],
            missing_recipients=[_identifier("vietnam")],
            expected=3,
            received=2,
        )

    _install_client(
        monkeypatch, broadcast_message_streaming=broadcast_message_streaming
    )

    chunks = await _collect(
        tools.get_all_farms_yield_inventory_streaming("how much coffee?")
    )

    assert chunks == [
        "Brazil Coffee Farm : 100 lb\n",
        "Incomplete answer: 2 of 3 farms gave no usable reply: "
        f"{COLOMBIA} returned an error (boom); {VIETNAM} did not reply at all.\n",
    ]


async def test_streaming_broadcast_timeout_with_nothing_received(monkeypatch):
    async def broadcast_message_streaming(request, *, recipients, context):
        raise A2ABroadcastTimeoutError(expected=3, received=0, timed_out=True)
        yield  # pragma: no cover - makes this an async generator

    _install_client(
        monkeypatch, broadcast_message_streaming=broadcast_message_streaming
    )

    chunks = await _collect(
        tools.get_all_farms_yield_inventory_streaming("how much coffee?")
    )

    [chunk] = chunks
    assert chunk.startswith("Error: Broadcast timed out.")


async def test_streaming_broadcast_skips_an_unusable_reply_without_an_error_line(
    monkeypatch,
):
    async def broadcast_message_streaming(request, *, recipients, context):
        yield StreamResponse(message=_farm_message("Brazil Coffee Farm", "100 lb"))
        yield StreamResponse(message=_farm_message(VIETNAM, ""))
        yield StreamResponse(message=_farm_message(COLOMBIA, "70 lb"))

    _install_client(
        monkeypatch, broadcast_message_streaming=broadcast_message_streaming
    )

    chunks = await _collect(
        tools.get_all_farms_yield_inventory_streaming("how much coffee?")
    )

    assert chunks == [
        "Brazil Coffee Farm : 100 lb\n",
        f"{COLOMBIA} : 70 lb\n",
        "Incomplete answer: 1 of 3 farms gave no usable reply: "
        f"{VIETNAM} gave no usable reply.\n",
    ]
    assert not any("Unknown response format" in chunk for chunk in chunks)
