# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""A2A executor shared by the supplier and logistics agents."""

import logging
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import AgentCard, Message, Part, Role
from a2a.utils.errors import (
    ContentTypeNotSupportedError,
    InternalError,
    UnsupportedOperationError,
)

from agents.supply_chain.common.envelope import decode
from agents.supply_chain.common.member import MemberAgent

logger = logging.getLogger("lungo.supply_chain.member_executor")


class MemberAgentExecutor(AgentExecutor):
    def __init__(self, agent: MemberAgent, card: AgentCard):
        self.agent = agent
        self.card = card

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Answer one envelope with a single final ``Message`` (no ``Task``).

        a2a-sdk 1.x rejects a ``Message`` enqueued after a ``Task`` for the
        same request, so the reply is always one message.
        """
        if not context or not context.message or not context.message.parts:
            logger.error("Invalid request parameters: %s", context)
            raise ContentTypeNotSupportedError()
        request = decode(context.get_user_input())
        if request is None:
            logger.error("Request is not a supply chain envelope")
            raise ContentTypeNotSupportedError()

        try:
            response = await self.agent.handle(request)
            message = Message(
                message_id=str(uuid4()),
                role=Role.ROLE_AGENT,
                metadata={"name": self.card.name},
                parts=[Part(text=response.encode())],
            )
            await event_queue.enqueue_event(message)
        except Exception as e:
            logger.error(
                "Error handling %s for %s: %s", request.kind, self.agent.party, e
            )
            raise InternalError() from e

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> None:
        raise UnsupportedOperationError()
