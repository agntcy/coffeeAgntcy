# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""The executor enqueues exactly one Message and rejects non-envelope input."""

from types import SimpleNamespace

import pytest
from a2a.types import Role
from a2a.utils.errors import ContentTypeNotSupportedError, InternalError

from agents.supply_chain.common.envelope import Envelope, decode
from agents.supply_chain.common.member import MemberAgent
from agents.supply_chain.common.member_executor import MemberAgentExecutor
from agents.supply_chain.logistics.card import AGENT_CARD
from tests.helpers.supply_chain_fakes import FakeLLM


class _Queue:
    def __init__(self):
        self.events = []

    async def enqueue_event(self, event):
        self.events.append(event)


def _context(text: str | None):
    parts = [SimpleNamespace(text=text)] if text is not None else []
    return SimpleNamespace(
        message=SimpleNamespace(parts=parts), get_user_input=lambda: text
    )


def _envelope(to=("logistics",)) -> Envelope:
    return Envelope(
        run_id="r1",
        seq=1,
        sender="moderator",
        to=to,
        kind="negotiation",
        case="explicit",
        body="Hi",
    )


async def test_one_message_reply_with_agent_name_metadata():
    executor = MemberAgentExecutor(
        MemberAgent("logistics", FakeLLM("Standard is 3 days.")), AGENT_CARD
    )
    queue = _Queue()
    await executor.execute(_context(_envelope().encode()), queue)

    [message] = queue.events
    assert message.role == Role.ROLE_AGENT
    assert dict(message.metadata)["name"] == "Logistics agent"
    reply = decode(message.parts[0].text)
    assert (reply.kind, reply.sender, reply.body) == (
        "negotiation",
        "logistics",
        "Standard is 3 days.",
    )


async def test_unaddressed_request_still_returns_one_noop_message():
    executor = MemberAgentExecutor(MemberAgent("logistics", FakeLLM()), AGENT_CARD)
    queue = _Queue()
    await executor.execute(_context(_envelope(to=("supplier_a",)).encode()), queue)
    assert [decode(e.parts[0].text).kind for e in queue.events] == ["noop"]


@pytest.mark.parametrize("text", [None, "plain text", '{"scc": 2}'])
async def test_non_envelope_input_is_rejected(text):
    executor = MemberAgentExecutor(MemberAgent("logistics", FakeLLM()), AGENT_CARD)
    with pytest.raises(ContentTypeNotSupportedError):
        await executor.execute(_context(text), _Queue())


async def test_llm_failure_becomes_internal_error():
    class Boom(FakeLLM):
        async def ainvoke(self, messages):
            raise RuntimeError("llm down")

    executor = MemberAgentExecutor(MemberAgent("logistics", Boom()), AGENT_CARD)
    queue = _Queue()
    with pytest.raises(InternalError):
        await executor.execute(_context(_envelope().encode()), queue)
    assert queue.events == []
