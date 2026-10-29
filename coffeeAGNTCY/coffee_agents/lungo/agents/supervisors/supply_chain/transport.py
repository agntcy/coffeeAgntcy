# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Delivery of one moderator step to its remote addressees (design D3).

A step is one ``broadcast_message`` call over SLIM: the SDK opens a group
session with the addressed agents and each addressee answers the sender only.
``GroupTransport`` is the seam the moderator tests use.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any, Protocol
from uuid import uuid4

from a2a.client import ClientCallContext
from a2a.helpers import get_message_text
from a2a.types import AgentCard, Message, Part, Role, SendMessageRequest
from agntcy_app_sdk import get_agent_identifier
from agntcy_app_sdk.semantic.a2a import A2ABroadcastError
from opentelemetry import trace

from agents.supply_chain.common.envelope import Envelope, decode
from agents.supply_chain.common.fixtures import Party
from common.a2a_helpers import message_metadata, response_message

logger = logging.getLogger("lungo.supply_chain.transport")
_tracer = trace.get_tracer("lungo.supply_chain.transport")


def _channel(request: Envelope) -> str:
    """A group channel name that is used for this step only.

    Live finding (task 4.2b): when steps reuse one channel name (the SDK's
    default is the first addressee's topic) with different invitees, a later
    step can be delivered to nobody and time out. A fresh name per step
    avoids it: the same step sequence passes with it and fails without it.
    """
    return f"lungo/agents/scc-{request.run_id}-{request.seq}"


class TransportError(Exception):
    """A step could not be delivered, or a reply could not be read."""


class GroupTransport(Protocol):
    async def broadcast(
        self, request: Envelope, recipients: Sequence[Party], *, timeout: float
    ) -> list[Envelope]:
        """Deliver ``request`` to ``recipients`` and return their replies."""
        ...


class SlimGroupTransport:
    def __init__(
        self,
        client_factory: Any,
        cards: Mapping[Party, AgentCard],
        interceptors: Sequence[Any] = (),
    ):
        self._client_factory = client_factory
        self._cards = dict(cards)
        self._interceptors = list(interceptors)
        self._party_by_card_name = {card.name: party for party, card in cards.items()}
        self._client: Any | None = None

    async def _get_client(self, anchor: AgentCard) -> Any:
        # The client's own card only names the broadcast topic; the recipient
        # list decides who is invited.
        if self._client is None:
            self._client = await self._client_factory.create(
                anchor, interceptors=self._interceptors
            )
        return self._client

    async def broadcast(
        self, request: Envelope, recipients: Sequence[Party], *, timeout: float
    ) -> list[Envelope]:
        if not recipients:
            return []
        missing = [p for p in recipients if p not in self._cards]
        if missing:
            raise TransportError(f"no agent card for {', '.join(missing)}")
        cards = [self._cards[p] for p in recipients]
        message = SendMessageRequest(
            message=Message(
                message_id=str(uuid4()),
                role=Role.ROLE_USER,
                parts=[Part(text=request.encode())],
            )
        )
        context = ClientCallContext(state={"broadcast_agent_cards": cards})
        try:
            client = await self._get_client(cards[0])
            # The event middleware pairs a request with its replies by trace
            # id, so the call and its replies run inside one span. Without it
            # the middleware warns and drops every inbound event.
            with _tracer.start_as_current_span("supply_chain.broadcast"):
                responses = await client.broadcast_message(
                    message,
                    recipients=[get_agent_identifier(card) for card in cards],
                    context=context,
                    timeout=timeout,
                    broadcast_topic=_channel(request),
                )
        except A2ABroadcastError as e:
            raise TransportError(f"broadcast incomplete: {e}") from e
        except Exception as e:
            raise TransportError(f"broadcast failed: {e}") from e
        return [self._read(response) for response in responses]

    def _read(self, response: Any) -> Envelope:
        message = response_message(response)
        if message is None:
            raise TransportError("a reply carried no message")
        envelope = decode(get_message_text(message))
        if envelope is None:
            raise TransportError("a reply is not a supply chain envelope")
        # The sender named inside the envelope must be the agent whose card
        # stamped the reply, so one agent cannot answer as another.
        stamped = self._party_by_card_name.get(
            str(message_metadata(message).get("name") or "")
        )
        if stamped != envelope.sender:
            raise TransportError(
                f"reply claims sender {envelope.sender!r} but came from {stamped!r}"
            )
        return envelope
