# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils.errors import ServerError
from a2a.types import (
    UnsupportedOperationError,
    JSONRPCResponse,
    ContentTypeNotSupportedError,
    InternalError,
    Message,
    Role,
    Part,
    TextPart,
    Task)

from a2a.utils import (
    new_task,
)

from agents.logistics.farm.agent import FarmAgent
from agents.logistics.farm.card import AGENT_CARD

logger = logging.getLogger("lungo.logistic_farm_agent.agent_executor")

class FarmAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = FarmAgent()
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)

    def _validate_request(self, context: RequestContext) -> JSONRPCResponse | None:
        """Validates the incoming request."""
        if not context or not context.message or not context.message.parts:
            logger.error("Invalid request parameters: %s", context)
            return JSONRPCResponse(error=ContentTypeNotSupportedError())
        return None
    
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
        - Create and enqueue a new Task if one does not exist.
        - Invoke the FarmAgent to advance the order (e.g., toward HANDOVER_TO_SHIPPER) or
          generate a status/update message.
        - Enqueue the agent's response as a Message event.

        May emit: Task, Message, TaskStatusUpdateEvent, TaskArtifactUpdateEvent.
        Returns after the agent completes processing or yields control.

        Args:
            context: Request context containing the incoming Message, Task (if any), and metadata.
            event_queue: Event queue used to publish resulting events.
        """

        logger.debug("Received message request: %s", context.message)

        validation_error = self._validate_request(context)
        if validation_error:
            await event_queue.enqueue_event(validation_error)
            return
        
        prompt = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        try:
            output = await self.agent.ainvoke(prompt)
        
            message = Message(
                message_id=str(uuid4()),
                role=Role.agent,
                metadata={"name": self.agent_card["name"]},
                parts=[Part(TextPart(text=output))],
            )

            logger.info("agent output message: %s", message)

            await event_queue.enqueue_event(message)            
        except Exception as e:
            logger.error(f'An error occurred while streaming the yield estimate response: {e}')
            raise ServerError(error=InternalError()) from e
        
    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        """Cancel this agent's execution for the given request context."""
        raise ServerError(error=UnsupportedOperationError())