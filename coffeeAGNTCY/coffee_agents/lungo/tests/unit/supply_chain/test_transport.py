# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""SlimGroupTransport with a fake SLIM client (design D3, live finding 4.2b)."""

from __future__ import annotations

import pytest
from a2a.types import Message, Part, Role, SendMessageResponse
from agntcy_app_sdk import get_agent_identifier
from agntcy_app_sdk.semantic.a2a import A2ABroadcastError
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from agents.supervisors.supply_chain import transport as transport_module
from agents.supervisors.supply_chain.transport import (
    SlimGroupTransport,
    TransportError,
    _channel,
)
from agents.supply_chain.common.envelope import Envelope
from agents.supply_chain.logistics.card import AGENT_CARD as LOGISTICS_CARD
from agents.supply_chain.supplier.card import AGENT_CARDS as SUPPLIER_CARDS

CARDS = {"logistics": LOGISTICS_CARD, **SUPPLIER_CARDS}


def _request(seq: int = 1, to=("supplier_a",)) -> Envelope:
    return Envelope(
        run_id="r1",
        seq=seq,
        sender="buyer",
        to=tuple(to),
        kind="negotiation",
        body="offer",
    )


def _reply(
    request: Envelope, party: str, *, card_name: str | None = None
) -> SendMessageResponse:
    envelope = Envelope(
        run_id=request.run_id,
        seq=request.seq,
        sender=party,
        to=(request.sender,),
        kind="negotiation",
        reply_to=request.seq,
        body="ok",
    )
    name = card_name if card_name is not None else CARDS[party].name
    return SendMessageResponse(
        message=Message(
            message_id=f"m-{party}",
            role=Role.ROLE_AGENT,
            metadata={"name": name},
            parts=[Part(text=envelope.encode())],
        )
    )


class FakeSlimClient:
    def __init__(self, factory: FakeClientFactory):
        self._factory = factory

    async def broadcast_message(
        self, message, *, recipients, context, timeout, broadcast_topic=None
    ):
        self._factory.calls.append(
            {
                "recipients": recipients,
                "cards": context.state["broadcast_agent_cards"],
                "timeout": timeout,
                "topic": broadcast_topic,
            }
        )
        self._factory.span_contexts.append(trace.get_current_span().get_span_context())
        if self._factory.error is not None:
            raise self._factory.error
        return self._factory.replies


class FakeClientFactory:
    def __init__(self, replies=(), error: Exception | None = None):
        self.replies = list(replies)
        self.error = error
        self.calls: list[dict] = []
        self.span_contexts: list = []
        self.created: list[tuple] = []

    async def create(self, card, interceptors=()):
        self.created.append((card, list(interceptors)))
        return FakeSlimClient(self)


async def test_each_step_uses_a_channel_of_its_own():
    factory = FakeClientFactory()
    transport = SlimGroupTransport(factory, CARDS)
    for seq in (1, 2, 3):
        request = _request(seq)
        factory.replies = [_reply(request, "supplier_a")]
        await transport.broadcast(request, ["supplier_a"], timeout=5)
    topics = [call["topic"] for call in factory.calls]
    assert len(set(topics)) == 3
    assert topics[0] == _channel(_request(1)) == "lungo/agents/scc-r1-1"


async def test_channel_differs_between_runs_with_the_same_seq():
    other = _request(1).model_copy(update={"run_id": "r2"})
    assert _channel(_request(1)) != _channel(other)


async def test_recipients_are_the_addressed_agents_only():
    request = _request(to=("supplier_c", "logistics"))
    factory = FakeClientFactory(
        [_reply(request, "supplier_c"), _reply(request, "logistics")]
    )
    transport = SlimGroupTransport(factory, CARDS)
    replies = await transport.broadcast(
        request, ["supplier_c", "logistics"], timeout=7.5
    )
    call = factory.calls[0]
    assert call["recipients"] == [
        get_agent_identifier(SUPPLIER_CARDS["supplier_c"]),
        get_agent_identifier(LOGISTICS_CARD),
    ]
    assert call["cards"] == [SUPPLIER_CARDS["supplier_c"], LOGISTICS_CARD]
    assert call["timeout"] == 7.5
    assert [r.sender for r in replies] == ["supplier_c", "logistics"]


async def test_the_client_is_created_once_with_the_interceptors():
    sentinel = object()
    factory = FakeClientFactory()
    transport = SlimGroupTransport(factory, CARDS, interceptors=[sentinel])
    for seq in (1, 2):
        request = _request(seq)
        factory.replies = [_reply(request, "supplier_a")]
        await transport.broadcast(request, ["supplier_a"], timeout=5)
    assert len(factory.created) == 1
    assert factory.created[0][1] == [sentinel]


async def test_no_recipients_means_no_call():
    factory = FakeClientFactory()
    transport = SlimGroupTransport(factory, CARDS)
    assert await transport.broadcast(_request(), [], timeout=5) == []
    assert factory.calls == [] and factory.created == []


async def test_an_unknown_recipient_is_refused_before_any_call():
    factory = FakeClientFactory()
    transport = SlimGroupTransport(factory, {"logistics": LOGISTICS_CARD})
    with pytest.raises(TransportError, match="supplier_a"):
        await transport.broadcast(_request(), ["supplier_a"], timeout=5)
    assert factory.calls == []


async def test_a_reply_cannot_claim_another_sender():
    request = _request(to=("supplier_a",))
    forged = _reply(request, "supplier_a", card_name=SUPPLIER_CARDS["supplier_b"].name)
    transport = SlimGroupTransport(FakeClientFactory([forged]), CARDS)
    with pytest.raises(TransportError, match="claims sender"):
        await transport.broadcast(request, ["supplier_a"], timeout=5)


async def test_a_reply_without_a_card_name_is_refused():
    request = _request()
    nameless = _reply(request, "supplier_a", card_name="")
    transport = SlimGroupTransport(FakeClientFactory([nameless]), CARDS)
    with pytest.raises(TransportError, match="claims sender"):
        await transport.broadcast(request, ["supplier_a"], timeout=5)


async def test_a_reply_that_is_not_an_envelope_is_refused():
    reply = SendMessageResponse(
        message=Message(
            message_id="m",
            role=Role.ROLE_AGENT,
            metadata={"name": SUPPLIER_CARDS["supplier_a"].name},
            parts=[Part(text="hello")],
        )
    )
    transport = SlimGroupTransport(FakeClientFactory([reply]), CARDS)
    with pytest.raises(TransportError, match="not a supply chain envelope"):
        await transport.broadcast(_request(), ["supplier_a"], timeout=5)


async def test_a_reply_without_a_message_is_refused():
    transport = SlimGroupTransport(FakeClientFactory([SendMessageResponse()]), CARDS)
    with pytest.raises(TransportError, match="no message"):
        await transport.broadcast(_request(), ["supplier_a"], timeout=5)


async def test_a_broadcast_error_becomes_a_transport_error():
    error = A2ABroadcastError(
        expected=2, received=1, missing_recipients=["supplier_b"], timed_out=True
    )
    transport = SlimGroupTransport(FakeClientFactory(error=error), CARDS)
    with pytest.raises(TransportError, match="broadcast incomplete.*supplier_b"):
        await transport.broadcast(_request(), ["supplier_a"], timeout=5)


async def test_any_other_error_becomes_a_transport_error():
    transport = SlimGroupTransport(
        FakeClientFactory(error=RuntimeError("session closed")), CARDS
    )
    with pytest.raises(TransportError, match="broadcast failed: session closed"):
        await transport.broadcast(_request(), ["supplier_a"], timeout=5)


async def test_a_step_runs_inside_one_span_for_the_event_middleware(monkeypatch):
    """The event middleware needs a trace id to pair a request with its replies."""
    monkeypatch.setattr(
        transport_module, "_tracer", TracerProvider().get_tracer("test")
    )
    factory = FakeClientFactory()
    transport = SlimGroupTransport(factory, CARDS)
    seen = []
    for seq in (1, 2):
        request = _request(seq)
        factory.replies = [_reply(request, "supplier_a")]
        await transport.broadcast(request, ["supplier_a"], timeout=5)
        seen.append(factory.span_contexts[-1])
    assert all(context.is_valid for context in seen)
    assert seen[0].trace_id != seen[1].trace_id
    # The span ends with the step.
    assert not trace.get_current_span().get_span_context().is_valid
