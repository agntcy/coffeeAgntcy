# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Delivery of one moderator step to its remote addressees (design D3).

A step is one ``broadcast_message`` call over SLIM: the SDK opens a group
session with the addressed agents and each addressee answers the sender only.
``GroupTransport`` is the seam the moderator tests use.
"""

from __future__ import annotations

import asyncio
import contextlib
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


def _report_broken_connection(client: Any) -> None:
    """Tell the SDK that the SLIM connection under ``client`` may be dead.

    Every SLIM transport in the process shares one connection, and closing the
    discarded client only gives back its own share. While another transport
    still holds a share, the SDK keeps handing the same connection to the next
    client, which would be built on the connection that just failed. Reporting
    it makes the next client open a new one. Transports already on the old
    connection keep it until the last of them closes. A client without a SLIM
    transport (a test double) has nothing to report.
    """
    report = getattr(getattr(client, "transport", None), "mark_connection_broken", None)
    if report is not None:
        with contextlib.suppress(Exception):
            report()


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
        self._client_lock = asyncio.Lock()
        self._client_users: dict[int, int] = {}

    @contextlib.asynccontextmanager
    async def _lease_client(self, anchor: AgentCard):
        # The client's own card only names the broadcast topic; the recipient
        # list decides who is invited.
        async with self._client_lock:
            if self._client is None:
                self._client = await self._client_factory.create(
                    anchor, interceptors=self._interceptors
                )
            client = self._client
            key = id(client)
            self._client_users[key] = self._client_users.get(key, 0) + 1
        broken = False
        # A broken client is dropped. Only a transport failure says the shared
        # SLIM connection under it may be dead too; a cancel or a missing-reply
        # timeout says nothing about the connection.
        connection_broken = False
        try:
            yield client
        except A2ABroadcastError as e:
            # A missing-reply timeout stays reusable (timed_out, transport_error
            # None). A transport failure after some replies arrives wrapped.
            broken = connection_broken = e.transport_error is not None
            raise
        except asyncio.CancelledError:
            # The broadcast was in flight. The next run starts a new client.
            broken = True
            raise
        except Exception:
            broken = connection_broken = True
            raise
        finally:
            # Concurrent runs share the client: close a broken one only
            # after its last user is done.
            async with self._client_lock:
                if broken and self._client is client:
                    self._client = None
                    if connection_broken:
                        _report_broken_connection(client)
                self._client_users[key] -= 1
                close = self._client_users[key] == 0 and self._client is not client
                if close:
                    del self._client_users[key]
            if close:
                with contextlib.suppress(Exception):
                    await client.close()

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
            async with self._lease_client(cards[0]) as client:
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
        # The envelope's sender must match the card name the replying executor
        # put in the message metadata. This catches a reply built for the wrong
        # party; it is not authentication (the metadata is self-declared).
        stamped = self._party_by_card_name.get(
            str(message_metadata(message).get("name") or "")
        )
        if stamped != envelope.sender:
            raise TransportError(
                f"reply claims sender {envelope.sender!r} "
                f"but the metadata name maps to {stamped!r}"
            )
        return envelope
