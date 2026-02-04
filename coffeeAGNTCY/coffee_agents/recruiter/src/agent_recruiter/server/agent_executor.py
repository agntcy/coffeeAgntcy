# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import time
from uuid import uuid4
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    UnsupportedOperationError,
    ContentTypeNotSupportedError,
    InternalError,
    Message,
    Role,
    Part,
    TextPart,
    DataPart,
    Task,
    TaskStatus,
    TaskState,
    TaskStatusUpdateEvent,
)
from a2a.utils import (
    new_task,
)
from a2a.utils.errors import ServerError

from agent_recruiter.common.logging import get_logger
from agent_recruiter.recruiter import RecruiterTeam
from agent_recruiter.server.card import AGENT_CARD
from agent_recruiter.server.event_converter import (
    convert_adk_to_a2a_events,
    create_working_status_event,
)

logger = get_logger(__name__)


class RecruiterAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = RecruiterTeam()
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)

    def _validate_request(self, context: RequestContext) -> bool:
        """Validates the incoming request.

        Returns:
            True if valid, False otherwise.
        """
        if not context or not context.message or not context.message.parts:
            logger.error("Invalid request parameters: %s", context)
            return False
        return True

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the agent's logic, streaming events progressively.

        This method streams intermediate events (tool calls, agent handoffs,
        status updates) as they occur, providing real-time feedback to clients.
        """
        logger.debug("Received message request: %s", context.message)

        if not self._validate_request(context):
            raise ServerError(error=ContentTypeNotSupportedError())

        prompt = context.get_user_input()
        task = context.current_task
        if not task:
            if context.message is None:
                raise ServerError(error=ContentTypeNotSupportedError())
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        task_id = task.id

        # Extract context_id and session_id from A2A context
        # context_id is used for A2A events, session_id for ADK session management
        context_id = context.context_id or str(uuid4())
        session_id = context_id  # Use same ID for both

        # Extract user_id from message metadata, with fallback
        user_id = "anonymous"
        if context.message and context.message.metadata:
            user_id = context.message.metadata.get("user_id", "anonymous")

        logger.debug(f"Processing request: user_id={user_id}, session_id={session_id}")

        try:
            t0 = time.time()

            # Emit initial "working" status
            await event_queue.enqueue_event(
                create_working_status_event(
                    task_id=task_id,
                    context_id=context_id,
                    message_text="Processing your request...",
                    metadata={"event_type": "processing_started"},
                )
            )

            final_response = None
            event_count = 0

            # Stream events from the ADK runner
            async for adk_event in self.agent.stream(prompt, user_id, session_id):
                event_count += 1

                # Convert and emit intermediate events
                for a2a_event in convert_adk_to_a2a_events(
                    adk_event, task_id, context_id, self.agent_card["name"]
                ):
                    await event_queue.enqueue_event(a2a_event)

                # Capture final response
                if adk_event.is_final_response():
                    if adk_event.content and adk_event.content.parts:
                        final_response = "".join(
                            p.text or "" for p in adk_event.content.parts
                        )

            t1 = time.time()
            logger.debug(
                f"Agent execution completed in {t1 - t0:.2f} seconds. "
                f"Processed {event_count} events."
            )

            # Get found agent records from session state
            found_records = await self.agent.get_found_agent_records(
                user_id, session_id
            )

            # Get evaluation results from session state
            evaluation_results = await self.agent.get_evaluation_results(
                user_id, session_id
            )

            # Build final message parts
            parts = [
                Part(root=TextPart(text=final_response or "No response generated."))
            ]

            # Include found agent records as DataPart if any exist
            if found_records:
                parts.append(
                    Part(
                        root=DataPart(
                            data=found_records,
                            metadata={"type": "found_agent_records"},
                        )
                    )
                )

            # Include evaluation results as DataPart if any exist
            if evaluation_results:
                parts.append(
                    Part(
                        root=DataPart(
                            data=evaluation_results,
                            metadata={"type": "evaluation_results"},
                        )
                    )
                )

            # Create the final message
            final_message = Message(
                message_id=str(uuid4()),
                role=Role.agent,
                metadata={"name": self.agent_card["name"]},
                parts=parts,
            )

            # Send final status update with completed state
            # The A2A protocol expects streaming to end with a TaskStatusUpdateEvent
            # with final=True, not a separate Message
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task_id,
                    context_id=context_id,
                    final=True,
                    status=TaskStatus(
                        state=TaskState.completed,
                        message=final_message,
                    ),
                )
            )

        except Exception as e:
            logger.error(f"Error during streaming execution: {e}")
            raise ServerError(error=InternalError()) from e

    async def cancel(
        self, _request: RequestContext, _event_queue: EventQueue
    ) -> Task | None:
        """Cancel this agent's execution for the given request context."""
        raise ServerError(error=UnsupportedOperationError())
