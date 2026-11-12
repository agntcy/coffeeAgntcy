# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import time
from uuid import uuid4
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    Message,
    Role,
    Task,
    TaskStatus,
    TaskState,
    TaskStatusUpdateEvent,
)
from a2a.utils.errors import (
    ContentTypeNotSupportedError,
    InternalError,
    UnsupportedOperationError,
)

from agent_recruiter.common.a2a_helpers import (
    data_part,
    message_metadata,
    part_data,
    part_kind,
    part_metadata,
    text_part,
    to_struct,
)
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
        self.agent_name = AGENT_CARD.name

    def _validate_request(self, context: RequestContext) -> bool:
        """Validates the incoming request.

        Returns:
            True if valid, False otherwise.
        """
        if not context or not context.message or not context.message.parts:
            logger.error("Invalid request parameters: {}", context)
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
        if not self._validate_request(context):
            raise ContentTypeNotSupportedError()

        prompt = context.get_user_input()

        logger.info(f"[agent_executor] Received prompt: {prompt!r}")

        # Extract DataParts from the incoming A2A message.
        # The Lungo supervisor may send agent records (e.g. for evaluation)
        # as DataParts alongside the text prompt.  We seed them into the
        # session state so that downstream sub-agents (like agent_evaluator)
        # can access them immediately.
        initial_state_overrides: dict = {}
        if context.message and context.message.parts:
            for part in context.message.parts:
                if part_kind(part) != "data":
                    continue
                meta_type = part_metadata(part).get("type")
                data = part_data(part)
                if meta_type == "found_agent_records" and isinstance(data, dict):
                    initial_state_overrides["found_agent_records"] = data
                    logger.info(
                        "[agent_executor] Extracted {} found_agent_records from incoming DataPart",
                        len(data),
                    )
                elif meta_type == "evaluation_criteria" and isinstance(data, list):
                    initial_state_overrides["evaluation_criteria"] = data
                    logger.info(
                        "[agent_executor] Extracted {} evaluation_criteria from incoming DataPart",
                        len(data),
                    )

        task = context.current_task
        if not task:
            if context.message is None:
                raise ContentTypeNotSupportedError()
            task = Task(
                id=context.task_id or str(uuid4()),
                context_id=context.context_id or str(uuid4()),
                status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
                history=[context.message],
            )
            await event_queue.enqueue_event(task)

        task_id = task.id

        # Extract context_id and session_id from A2A context
        # context_id is used for A2A events, session_id for ADK session management
        context_id = context.context_id or str(uuid4())
        session_id = context_id  # Use same ID for both

        # Extract user_id from message metadata, with fallback
        user_id = "anonymous"
        user_id = message_metadata(context.message).get("user_id", user_id)

        logger.info(
            f"[agent_executor] Processing: user_id={user_id}, session_id={session_id}"
        )

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
            async for adk_event in self.agent.stream(
                prompt,
                user_id,
                session_id,
                initial_state_overrides=initial_state_overrides or None,
            ):
                event_count += 1

                # Convert and emit intermediate events
                for a2a_event in convert_adk_to_a2a_events(
                    adk_event, task_id, context_id, self.agent_name
                ):
                    await event_queue.enqueue_event(a2a_event)

                # Capture final response
                if adk_event.is_final_response():
                    if adk_event.content and adk_event.content.parts:
                        final_response = "".join(
                            p.text or "" for p in adk_event.content.parts
                        )

            t1 = time.time()
            logger.info(
                f"Agent execution completed in {t1 - t0:.2f}s. "
                f"Processed {event_count} events. user_id={user_id}, session_id={session_id}"
            )

            # Get found agent records from session state
            found_records = await self.agent.get_found_agent_records(
                user_id, session_id
            )
            logger.info(
                f"[agent_executor] get_found_agent_records returned {len(found_records)} records: "
                f"{list(found_records.keys()) if found_records else '(empty)'}"
            )

            # Get evaluation results from session state
            evaluation_results = await self.agent.get_evaluation_results(
                user_id, session_id
            )
            logger.info(
                f"[agent_executor] get_evaluation_results returned {len(evaluation_results)} results: "
                f"{list(evaluation_results.keys()) if evaluation_results else '(empty)'}"
            )

            # Build final message parts
            parts = [text_part(final_response or "No response generated.")]

            # Include found agent records as DataPart if any exist
            if found_records:
                logger.info(
                    f"[agent_executor] Including {len(found_records)} agent records in response DataPart"
                )
                parts.append(
                    data_part(found_records, metadata={"type": "found_agent_records"})
                )
            else:
                logger.warning(
                    "[agent_executor] No found_records to include in response (empty or None)"
                )

            # Include evaluation results as DataPart if any exist
            if evaluation_results:
                logger.info(
                    f"[agent_executor] Including {len(evaluation_results)} evaluation results in response DataPart"
                )
                parts.append(
                    data_part(
                        evaluation_results, metadata={"type": "evaluation_results"}
                    )
                )
            else:
                logger.debug(
                    "[agent_executor] No evaluation_results to include in response"
                )

            # Create the final message
            final_message = Message(
                message_id=str(uuid4()),
                role=Role.ROLE_AGENT,
                metadata=to_struct({"name": self.agent_name}),
                parts=parts,
            )

            # Send final status update with completed state. a2a-sdk 1.x has no
            # ``final`` flag: the terminal task state ends the stream.
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task_id,
                    context_id=context_id,
                    status=TaskStatus(
                        state=TaskState.TASK_STATE_COMPLETED,
                        message=final_message,
                    ),
                )
            )

        except Exception as e:
            logger.error(f"Error during streaming execution: {e}")
            raise InternalError() from e

    async def cancel(
        self, _request: RequestContext, _event_queue: EventQueue
    ) -> Task | None:
        """Cancel this agent's execution for the given request context."""
        raise UnsupportedOperationError()
