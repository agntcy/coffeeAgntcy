# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Store remote A2A Agent Connections in a custom class to manage different connection 
types. Initial implementation for simple HTTPX-based connections but will be extended
to support other connection types in A2A and agntcy app-sdk in the future.
"""

from typing import Callable, TypeAlias
import httpx
from a2a.client import ClientFactory, ClientConfig
from a2a.types import (
    AgentCard,
    Task,
    Message,
    MessageSendParams,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    JSONRPCError,
    JSONParseError,
    InvalidRequestError,
    MethodNotFoundError,
    InvalidParamsError,
    InternalError,
    TaskNotFoundError,
    TaskNotCancelableError,
    PushNotificationNotSupportedError,
    UnsupportedOperationError,
    ContentTypeNotSupportedError,
    InvalidAgentResponseError,
)
from loguru import logger

from agent_recruiter.interviewers.a2a.generic_task_callback import GenericTaskUpdateCallback

JSON_RPC_ERROR_TYPES: TypeAlias = (
    JSONRPCError
    | JSONParseError
    | InvalidRequestError
    | MethodNotFoundError
    | InvalidParamsError
    | InternalError
    | TaskNotFoundError
    | TaskNotCancelableError
    | PushNotificationNotSupportedError
    | UnsupportedOperationError
    | ContentTypeNotSupportedError
    | InvalidAgentResponseError
)

TaskCallbackArg: TypeAlias = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback: TypeAlias = Callable[[TaskCallbackArg, AgentCard], Task]


class RemoteAgentConnections:
    """A class to hold the connections to the remote agents."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        agent_card: AgentCard,
    ):
        # Create client configuration
        config = ClientConfig(
            httpx_client=client,
            streaming=True,  # Enable streaming support
        )

        # Create factory and client
        factory = ClientFactory(config)
        self.agent_client = factory.create(agent_card)
        self.card = agent_card

    def get_agent(self) -> AgentCard:
        return self.card

    async def send_message(
        self,
        request: MessageSendParams,
        task_callback: TaskUpdateCallback | None = None,
        stream: bool | None = None,
    ) -> Task | Message | JSON_RPC_ERROR_TYPES | None:
        """Send a message to the remote agent.

        The new Client API automatically handles streaming vs non-streaming
        based on agent capabilities and client configuration.
        """
        # Set up task callback
        if task_callback is None:
            task_callback = GenericTaskUpdateCallback().task_callback

        # The request already contains a properly formatted Message
        # Just use it directly
        message = request.message

        task = None
        first_message: Message | None = None

        try:
            # The send_message method returns AsyncIterator automatically
            # It handles both streaming and non-streaming based on config
            async for response in self.agent_client.send_message(message):
                logger.debug(
                    "received response from remote agent",
                    extra={
                        "response_type": type(response).__name__,
                        "response": response,
                    },
                )

                # Response is tuple[Task, Update] or Message
                if isinstance(response, Message):
                    # Direct message response — don't return immediately.
                    # Some agents send a Message followed by more streamed
                    # data; returning early causes the A2A SDK to raise
                    # "received a streamed Message … after first response".
                    # Instead, capture the first Message and keep draining
                    # so the iterator is fully consumed.
                    if first_message is None:
                        first_message = response
                    continue

                # Streaming response: (Task, Update event or None)
                if isinstance(response, tuple):
                    task_update, event = response

                    # Update task via callback
                    if task_callback is not None:
                        if event is not None:
                            # Update event (TaskStatusUpdateEvent or TaskArtifactUpdateEvent)
                            task = task_callback(event, self.card)
                        else:
                            # Task object itself
                            task = task_callback(task_update, self.card)
                    else:
                        task = task_update

                    # Check if this is the final update
                    if event and hasattr(event, "final") and event.final:
                        break

            # Prefer the streaming task result; fall back to direct Message
            return task if task is not None else first_message

        except Exception as e:
            logger.error(
                f"Error sending message to agent: {e}",
                extra={
                    "agent_name": self.card.name,
                    "agent_url": self.card.url,
                    "error_type": type(e).__name__,
                },
            )
            # Try to return an appropriate error
            if hasattr(e, "error"):
                return e.error
            raise