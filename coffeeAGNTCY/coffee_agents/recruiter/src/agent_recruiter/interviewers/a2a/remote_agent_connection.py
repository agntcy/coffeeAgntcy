# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Store a remote A2A agent connection. The client is built with the a2a-sdk
ClientFactory over HTTP JSON-RPC, the only transport the recruiter uses.
"""

from typing import Callable, TypeAlias

import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.types import (
    AgentCard,
    Message,
    SendMessageRequest,
    StreamResponse,
    Task,
)
from loguru import logger

from agent_recruiter.interviewers.a2a.generic_task_callback import (
    GenericTaskUpdateCallback,
)

TaskUpdateCallback: TypeAlias = Callable[[StreamResponse, AgentCard], Task | None]


class RemoteAgentConnections:
    """Holds an A2A client connection to a remote agent."""

    def __init__(self, agent_client, agent_card: AgentCard):
        self.agent_client = agent_client
        self.card = agent_card

    @classmethod
    async def create(
        cls,
        client: httpx.AsyncClient,
        agent_card: AgentCard,
    ) -> "RemoteAgentConnections":
        # JSONRPC is the only transport needed: it is the factory default, so
        # the client is built from the card's JSONRPC interface (an interface
        # that declares protocol_version 0.3 gets the v0.3 compat transport).
        config = ClientConfig(httpx_client=client, streaming=True)
        agent_client = ClientFactory(config).create(agent_card)
        return cls(agent_client, agent_card)

    def get_agent(self) -> AgentCard:
        return self.card

    @property
    def url(self) -> str:
        """URL of the card's first interface, for logs."""
        interfaces = self.card.supported_interfaces
        return interfaces[0].url if interfaces else ""

    async def send_message(
        self,
        message: Message,
        task_callback: TaskUpdateCallback | None = None,
    ) -> Task | Message | None:
        """Send a message to the remote agent.

        The client handles streaming vs non-streaming based on the agent's
        capabilities and the client configuration. A failure raises (the
        a2a-sdk 1.x errors are exceptions, not returned values).
        """
        if task_callback is None:
            task_callback = GenericTaskUpdateCallback().task_callback

        task: Task | None = None
        first_message: Message | None = None

        try:
            async for response in self.agent_client.send_message(
                SendMessageRequest(message=message)
            ):
                logger.debug(
                    "received response from remote agent",
                    extra={
                        "response_type": response.WhichOneof("payload"),
                        "response": response,
                    },
                )

                if response.WhichOneof("payload") == "message":
                    # Direct message response - don't return immediately.
                    # Some agents send a Message followed by more streamed
                    # data; returning early would leave the iterator
                    # unconsumed. Capture the first Message and keep draining.
                    if first_message is None:
                        first_message = Message()
                        first_message.CopyFrom(response.message)
                    continue

                updated = task_callback(response, self.card)
                if updated is not None:
                    task = updated

            # Prefer the streaming task result; fall back to direct Message
            return task if task is not None else first_message

        except Exception as e:
            logger.error(
                f"Error sending message to agent: {e}",
                extra={
                    "agent_name": self.card.name,
                    "agent_url": self.url,
                    "error_type": type(e).__name__,
                },
            )
            raise
