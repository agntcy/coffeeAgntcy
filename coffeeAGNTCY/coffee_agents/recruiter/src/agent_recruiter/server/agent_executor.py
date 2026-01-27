# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from agent_recruiter.common.logging import get_logger
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
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
from a2a.utils.errors import ServerError

from agent_recruiter.recruiter import AGENT_CARD, RecruiterTeam

logger = get_logger(__name__)

class RecruiterAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = RecruiterTeam()
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
        Execute the agent's logic for a given request context.
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

        # try to get user_id and session_id from context
        user_id = "anonymous_user"
        session_id = "default_session"

        try:
            output = await self.agent.invoke(prompt, user_id=user_id, session_id=session_id)
        
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