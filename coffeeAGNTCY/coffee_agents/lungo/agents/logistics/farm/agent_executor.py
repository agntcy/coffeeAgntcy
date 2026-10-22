# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Message, Part, Role
from a2a.utils.errors import (
    ContentTypeNotSupportedError,
    InternalError,
    UnsupportedOperationError,
)

from agents.logistics.farm.agent import FarmAgent
from agents.logistics.farm.card import AGENT_CARD

logger = logging.getLogger("lungo.logistic_farm_agent.agent_executor")


class FarmAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = FarmAgent()

    def _validate_request(self, context: RequestContext) -> None:
        """Validates the incoming request."""
        if not context or not context.message or not context.message.parts:
            logger.error("Invalid request parameters: %s", context)
            raise ContentTypeNotSupportedError()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Run the logistic farm agent for a single incoming request.

        Responsibilities:
        - Validate the request payload.
        - Extract user input from the context.
        - Invoke the FarmAgent to advance the order (e.g., toward HANDOVER_TO_SHIPPER) or
          generate a status/update message.
        - Enqueue the agent's response as a single Message event (no Task).

        Returns after the agent completes processing.

        Args:
            context: Request context containing the incoming Message, Task (if any), and metadata.
            event_queue: Event queue used to publish resulting events.
        """

        logger.debug("Received message request: %s", context.message)

        self._validate_request(context)

        prompt = context.get_user_input()

        # Reply in message mode: a single final Message and no Task. a2a-sdk
        # 1.x rejects a Message enqueued after a Task for the same request.
        try:
            output = await self.agent.ainvoke(prompt)

            message = Message(
                message_id=str(uuid4()),
                role=Role.ROLE_AGENT,
                metadata={"name": AGENT_CARD.name},
                parts=[Part(text=output)],
            )

            logger.debug("agent output message: %s", message)

            await event_queue.enqueue_event(message)
        except Exception as e:
            logger.error(
                f"An error occurred while streaming the yield estimate response: {e}"
            )
            raise InternalError() from e

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> None:
        """Cancel this agent's execution for the given request context."""
        raise UnsupportedOperationError()
