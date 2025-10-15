# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Task, UnsupportedOperationError
from a2a.utils import new_agent_text_message
from a2a.utils.errors import ServerError

from agents.logistics.helpdesk.card import AGENT_CARD
from agents.logistics.helpdesk.store.base import OrderEventStore
from agents.logistics.helpdesk.store.event import OrderEvent
from agents.logistics.helpdesk.store.memory import InMemoryOrderEventStore


logger = logging.getLogger("lungo.helpdesk_agent.executor")

# Precompiled order ID patterns (32 hex chars). Extend if needed.
_ORDER_ID_PATTERNS = [re.compile(r"\b[a-f0-9]{32}\b", re.IGNORECASE)]


def extract_order_id(text: str) -> str:
    """
    Extract the first matching order id from text.
    Returns "unknown" if no pattern matches.
    """
    for pat in _ORDER_ID_PATTERNS:
        match = pat.search(text)
        if match:
            return match.group(0)
    return "unknown"


def parse_order_event_line(
        line: str,
        timestamp: Optional[datetime] = None,
) -> Optional[OrderEvent]:
    """
    Parse a logistic status line of the form:
      <STATE> | <Sender> -> <Receiver>: <Message body>

    Returns:
      OrderEvent if successfully parsed, else None.
    """
    raw = line.strip()
    if not raw:
        return None

    # Split state from remainder: "<STATE> | rest"
    parts = raw.split("|", 1)
    if len(parts) != 2:
        return None
    state = parts[0].strip()
    remainder = parts[1].strip()

    # Split sender -> receiver : message
    arrow_parts = remainder.split("->", 1)
    if len(arrow_parts) != 2:
        return None
    sender = arrow_parts[0].strip()
    recv_and_msg = arrow_parts[1].strip()

    recv_parts = recv_and_msg.split(":", 1)
    if len(recv_parts) != 2:
        return None
    receiver = recv_parts[0].strip()
    message = recv_parts[1].strip()

    order_id = extract_order_id(message)
    return OrderEvent(
        order_id=order_id,
        sender=sender,
        receiver=receiver,
        message=message,
        state=state,
        timestamp=timestamp or datetime.now(timezone.utc),
    )


class HelpdeskAgent:
    """
    Lightweight agent:
      - Receives user input.
      - Attempts to parse and persist an OrderEvent.
      - Returns an IDLE marker response.
    """

    def __init__(self, store: OrderEventStore):
        self.store = store

    async def invoke(self, context: RequestContext) -> str:
        prompt = context.get_user_input()
        logger.debug("HelpdeskAgent received chat: %s", prompt)

        if "IDLE" not in prompt:
            event = parse_order_event_line(prompt)
            if event:
                await self.store.append(event.order_id, event)
                logger.debug("Updated event list for %s: %s", event.order_id, await self.store.get(event.order_id))

        return f"{AGENT_CARD.name} IDLE"


class HelpdeskAgentExecutor(AgentExecutor):
    """
    Bridges the HelpdeskAgent into the A2A execution model.
    """

    def __init__(self, store: OrderEventStore | None = None):
        self.store = store or InMemoryOrderEventStore()
        self.agent = HelpdeskAgent(self.store)
        # Static card snapshot for protocol usage.
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)

    async def execute(
            self,
            context: RequestContext,
            event_queue: EventQueue,
    ) -> None:
        """
        Execute a single agent invocation and enqueue textual result.
        """
        result = await self.agent.invoke(context)
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(
            self,
            request: RequestContext,
            event_queue: EventQueue,
    ) -> Task | None:
        """
        Cancel is not supported for this simple agent.
        """
        raise ServerError(error=UnsupportedOperationError())
