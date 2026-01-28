# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import time
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
    DataPart,
    Task)
from a2a.utils import (
    new_task,
)
from a2a.utils.errors import ServerError

from agent_recruiter.common.logging import get_logger
from agent_recruiter.recruiter import RecruiterTeam
from agent_recruiter.server.card import AGENT_CARD

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

        # Extract session_id from A2A context_id (conversation context)
        session_id = context.context_id or str(uuid4())

        # Extract user_id from message metadata, with fallback
        user_id = "anonymous"
        if context.message and context.message.metadata:
            user_id = context.message.metadata.get("user_id", "anonymous")

        logger.debug(f"Processing request: user_id={user_id}, session_id={session_id}")

        try:
            t0 = time.time()
            result = await self.agent.invoke(prompt, user_id=user_id, session_id=session_id)
            t1 = time.time()
            logger.debug(f"Agent execution completed in {t1 - t0:.2f} seconds.")

            # Build message parts: text response + optional data part for records
            parts = [Part(TextPart(text=result["response"]))]

            # Include found agent records as DataPart if any exist
            if result.get("found_agent_records"):
                parts.append(Part(DataPart(
                    data=result["found_agent_records"],
                    metadata={"type": "found_agent_records"}
                )))

            message = Message(
                message_id=str(uuid4()),
                role=Role.agent,
                metadata={"name": self.agent_card["name"]},
                parts=parts,
            )

            await event_queue.enqueue_event(message)
        except Exception as e:
            logger.error(f'An error occurred while streaming the yield estimate response: {e}')
            raise ServerError(error=InternalError()) from e
        
    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        """Cancel this agent's execution for the given request context."""
        raise ServerError(error=UnsupportedOperationError())