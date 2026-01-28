# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Convert ADK events to A2A event types for streaming."""

from typing import Generator, Any
from uuid import uuid4

from google.adk.events.event import Event as AdkEvent
from a2a.types import (
    Message,
    Part,
    TextPart,
    DataPart,
    Role,
    TaskStatus,
    TaskState,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    Artifact,
)

from agent_recruiter.common.logging import get_logger

logger = get_logger(__name__)


def convert_adk_to_a2a_events(
    adk_event: AdkEvent,
    task_id: str,
    context_id: str,
    agent_name: str,
) -> Generator[TaskStatusUpdateEvent | TaskArtifactUpdateEvent, None, None]:
    """Convert an ADK Event to one or more A2A events.

    ADK events contain:
    - content: text, function_call, function_response
    - actions: transfer_to_agent, escalate, state_delta, artifact_delta
    - partial: whether this is a streaming chunk
    - author: which agent produced this event

    Args:
        adk_event: The ADK event to convert
        task_id: The A2A task ID to associate events with
        context_id: The A2A context ID for the conversation
        agent_name: The name of the agent for metadata

    Yields:
        A2A events (TaskStatusUpdateEvent or TaskArtifactUpdateEvent)
    """
    # Handle agent transfers (handoffs)
    if adk_event.actions.transfer_to_agent:
        logger.debug(
            f"Agent transfer: {adk_event.author} -> {adk_event.actions.transfer_to_agent}"
        )
        yield TaskStatusUpdateEvent(
            task_id=task_id,
            context_id=context_id,
            final=False,
            status=TaskStatus(
                state=TaskState.working,
                message=Message(
                    message_id=str(uuid4()),
                    role=Role.agent,
                    parts=[
                        Part(
                            root=TextPart(
                                text=f"Transferring to {adk_event.actions.transfer_to_agent}..."
                            )
                        )
                    ],
                    metadata={
                        "event_type": "agent_transfer",
                        "from_agent": adk_event.author,
                        "to_agent": adk_event.actions.transfer_to_agent,
                    },
                ),
            ),
        )

    # Handle escalation
    if adk_event.actions.escalate:
        logger.debug(f"Agent escalation from: {adk_event.author}")
        yield TaskStatusUpdateEvent(
            task_id=task_id,
            context_id=context_id,
            final=False,
            status=TaskStatus(
                state=TaskState.working,
                message=Message(
                    message_id=str(uuid4()),
                    role=Role.agent,
                    parts=[
                        Part(
                            root=TextPart(
                                text=f"Escalating from {adk_event.author}..."
                            )
                        )
                    ],
                    metadata={
                        "event_type": "escalation",
                        "from_agent": adk_event.author,
                    },
                ),
            ),
        )

    # Handle function calls (tool invocations) - only non-partial events
    function_calls = adk_event.get_function_calls()
    if function_calls and not adk_event.partial:
        for fc in function_calls:
            logger.debug(f"Tool call: {fc.name} by {adk_event.author}")
            # Safely convert args to dict for JSON serialization
            args_dict = dict(fc.args) if fc.args else {}
            yield TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                final=False,
                status=TaskStatus(
                    state=TaskState.working,
                    message=Message(
                        message_id=str(uuid4()),
                        role=Role.agent,
                        parts=[
                            Part(root=TextPart(text=f"Calling tool: {fc.name}"))
                        ],
                        metadata={
                            "event_type": "tool_call",
                            "tool_name": fc.name,
                            "tool_args": args_dict,
                            "author": adk_event.author,
                        },
                    ),
                ),
            )

    # Handle function responses (tool results) - only non-partial events
    function_responses = adk_event.get_function_responses()
    if function_responses and not adk_event.partial:
        for fr in function_responses:
            logger.debug(f"Tool response: {fr.name}")
            yield TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                final=False,
                status=TaskStatus(
                    state=TaskState.working,
                    message=Message(
                        message_id=str(uuid4()),
                        role=Role.agent,
                        parts=[
                            Part(root=TextPart(text=f"Tool {fr.name} completed"))
                        ],
                        metadata={
                            "event_type": "tool_response",
                            "tool_name": fr.name,
                            "author": adk_event.author,
                        },
                    ),
                ),
            )

    # Handle artifact updates
    if adk_event.actions.artifact_delta:
        for filename, version in adk_event.actions.artifact_delta.items():
            logger.debug(f"Artifact update: {filename} v{version}")
            yield TaskArtifactUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                artifact=Artifact(
                    name=filename,
                    artifact_id=str(uuid4()),
                    parts=[
                        Part(
                            root=DataPart(
                                data={"version": version},
                                metadata={"filename": filename},
                            )
                        )
                    ],
                ),
            )

    # Handle intermediate text content (non-partial, non-final)
    # Skip function calls/responses as they're handled above
    if (
        adk_event.content
        and adk_event.content.parts
        and not adk_event.partial
        and not function_calls
        and not function_responses
        and not adk_event.is_final_response()
    ):
        text_parts = [p.text for p in adk_event.content.parts if p.text]
        if text_parts:
            combined_text = "".join(text_parts)
            logger.debug(
                f"Intermediate text from {adk_event.author}: {combined_text[:100]}..."
            )
            yield TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                final=False,
                status=TaskStatus(
                    state=TaskState.working,
                    message=Message(
                        message_id=str(uuid4()),
                        role=Role.agent,
                        parts=[Part(root=TextPart(text=combined_text))],
                        metadata={
                            "event_type": "intermediate_response",
                            "author": adk_event.author,
                        },
                    ),
                ),
            )


def create_working_status_event(
    task_id: str,
    context_id: str,
    message_text: str,
    metadata: dict[str, Any] | None = None,
    final: bool = False,
) -> TaskStatusUpdateEvent:
    """Create a TaskStatusUpdateEvent with working state.

    Args:
        task_id: The task ID
        context_id: The context ID for the conversation
        message_text: Text to include in the status message
        metadata: Optional metadata to include
        final: Whether this is the final event

    Returns:
        A TaskStatusUpdateEvent with working state
    """
    return TaskStatusUpdateEvent(
        task_id=task_id,
        context_id=context_id,
        final=final,
        status=TaskStatus(
            state=TaskState.working,
            message=Message(
                message_id=str(uuid4()),
                role=Role.agent,
                parts=[Part(root=TextPart(text=message_text))],
                metadata=metadata,
            ),
        ),
    )
