# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
A2A Evaluator Agent implementation. Conduct evaluations of agents using the A2A protocol by sending
messages and evaluating responses related to predefined scenarios.
"""

import json
from types import TracebackType
from typing import Callable, Optional, Self, Type
from urllib.parse import urlparse
from uuid import uuid4

from a2a.client import A2ACardResolver
from a2a.types import AgentCard, AgentInterface, Message, Role, Task
from google.protobuf.json_format import MessageToDict
from httpx import AsyncClient
from loguru import logger
from rogue_sdk.types import Protocol, Scenarios, Transport

from agent_recruiter.common.a2a_helpers import (
    parts_text,
    task_text,
    text_part,
)
from agent_recruiter.interviewers.a2a.remote_agent_connection import (
    RemoteAgentConnections,
)
from agent_recruiter.interviewers.base_evaluator_agent import BaseEvaluatorAgent

# Hosts that mean "listen on every interface" and cannot be dialed by a client.
# Agents that bind to 0.0.0.0 often publish it in their card as the HTTP URL.
_UNDIALABLE_HOSTS = {"", "0.0.0.0", "::"}


def ensure_jsonrpc_interface(card: AgentCard, address: str) -> None:
    """Make sure ``card`` has an HTTP JSON-RPC interface the client can use.

    The a2a-sdk client factory matches ``protocol_binding`` exactly (``JSONRPC``)
    and dials the interface url as given. Cards in the wild break that in two
    ways: the binding is spelled in lowercase (``jsonrpc``, as the lungo farms
    publish it), or the url is missing or a wildcard bind address such as
    ``http://0.0.0.0:9999``. We just fetched the card from ``address``, so that
    address is known to be reachable; use it when the card offers nothing
    usable. The first usable interface is kept, with only its binding
    normalized, and becomes the card's only interface. The client factory
    prefers an interface that declares version ``1.0`` over the first match,
    so a second JSON-RPC interface (for example an undialable one) must not
    stay on the card.

    Interfaces for other transports (SLIM, NATS) are dropped in both cases,
    because the recruiter only speaks HTTP JSON-RPC.
    """
    jsonrpc = [
        i for i in card.supported_interfaces if i.protocol_binding.upper() == "JSONRPC"
    ]
    for interface in jsonrpc:
        host = urlparse(interface.url).hostname or ""
        if interface.url and host not in _UNDIALABLE_HOSTS:
            chosen = AgentInterface()
            chosen.CopyFrom(interface)
            chosen.protocol_binding = "JSONRPC"
            del card.supported_interfaces[:]
            card.supported_interfaces.append(chosen)
            return

    logger.warning(
        "Fetched agent card has no usable JSON-RPC interface - "
        "patching with evaluated_agent_address: {}",
        address,
    )
    # Keep the version the agent declared (JSON-RPC interfaces first, then any
    # interface). Without one, use 0.3: v0.3 servers and 1.x servers built with
    # v0.3 compat accept it (outside agents; the lungo farms are v1.0 only).
    version = next(
        (
            i.protocol_version
            for i in [*jsonrpc, *card.supported_interfaces]
            if i.protocol_version
        ),
        "0.3",
    )
    del card.supported_interfaces[:]
    card.supported_interfaces.append(
        AgentInterface(
            url=address,
            protocol_binding="JSONRPC",
            protocol_version=version,
        )
    )


class A2AEvaluatorAgent(BaseEvaluatorAgent):
    def __init__(
        self,
        evaluated_agent_address: str,
        transport: Optional[Transport],
        scenarios: Scenarios,
        business_context: Optional[str],
        headers: Optional[dict[str, str]] = None,
        debug: bool = False,
        deep_test_mode: bool = False,
        chat_update_callback: Optional[Callable[[dict], None]] = None,
        http_client: Optional[AsyncClient] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            evaluated_agent_address=evaluated_agent_address,
            protocol=Protocol.A2A,
            transport=transport,
            headers=headers,
            scenarios=scenarios,
            business_context=business_context,
            debug=debug,
            deep_test_mode=deep_test_mode,
            chat_update_callback=chat_update_callback,
            **kwargs,
        )
        self._http_client = http_client or AsyncClient(
            headers=headers or {},
            timeout=30,
        )
        self.__evaluated_agent_client: RemoteAgentConnections | None = None

    async def _get_evaluated_agent_client(self) -> RemoteAgentConnections:
        logger.debug("_get_evaluated_agent - enter")
        if self.__evaluated_agent_client is None:
            card_resolver = A2ACardResolver(
                self._http_client,
                self._evaluated_agent_address,
            )
            card = await card_resolver.get_agent_card()

            # Some agents serve a card the client cannot use as is (empty or
            # wildcard url, lowercase binding, only SLIM/NATS interfaces).
            ensure_jsonrpc_interface(card, self._evaluated_agent_address)

            self.__evaluated_agent_client = await RemoteAgentConnections.create(
                self._http_client,
                card,
            )

        return self.__evaluated_agent_client

    @staticmethod
    def _get_text_from_response(
        response: Task | Message,
    ) -> str | None:
        # TODO: add support for multi-model responses (audio, images, etc.)
        logger.debug(f"_get_text_from_response {response}")

        if isinstance(response, Message):
            return parts_text(list(response.parts))
        elif isinstance(response, Task):
            return task_text(response)

        return None

    async def _send_message_to_evaluated_agent(
        self,
        context_id: str,
        message: str,
    ) -> dict[str, str]:
        """
        Sends a message to the evaluated agent.
        :param message: the text to send to the other agent.
        :param context_id: The context ID of the conversation.
            Each conversation has a unique context_id. All messages in the conversation
            have the same context_id.
        :return: A dictionary containing the response from the evaluated agent.
            - "response": the response string. If there is no response
                from the other agent, the string is empty.
        """
        try:
            logger.info(
                "🔗 Making A2A call to evaluated agent",
                extra={
                    "message": message[:100] + "..." if len(message) > 100 else message,
                    "context_id": context_id,
                    "agent_url": self._evaluated_agent_address,
                },
            )

            self._add_message_to_chat_history(context_id, "user", message)

            agent_client = await self._get_evaluated_agent_client()
            logger.debug(
                "Sending message via RemoteAgentConnections",
                extra={
                    "card_name": agent_client.card.name,
                    "card_url": agent_client.url,
                    "card_streaming": agent_client.card.capabilities.streaming,
                },
            )
            response = await agent_client.send_message(
                Message(
                    context_id=context_id,
                    message_id=uuid4().hex,
                    role=Role.ROLE_USER,
                    parts=[text_part(message)],
                ),
            )

            if not response:
                logger.warning(
                    "_send_message_to_evaluated_agent - no response",
                    extra={
                        "protocol": "a2a",
                        "agent_url": self._evaluated_agent_address,
                        "context_id": context_id,
                    },
                )
                return {"response": ""}

            logger.info(
                "📨 Raw response from evaluated agent",
                extra={
                    "response_type": type(response).__name__,
                    "context_id": context_id,
                },
            )

            agent_response_text = (
                self._get_text_from_response(response) or "Not a text response"
            )

            self._add_message_to_chat_history(
                context_id,
                "assistant",
                agent_response_text,
            )

            logger.info(
                "✅ A2A call successful - received response from evaluated agent",
                extra={
                    "response_length": len(agent_response_text),
                    "response_preview": (
                        agent_response_text[:200] + "..."
                        if len(agent_response_text) > 200
                        else agent_response_text
                    ),
                    "context_id": context_id,
                    "agent_url": self._evaluated_agent_address,
                },
            )
            return {"response": json.dumps(MessageToDict(response))}
        except Exception as e:
            logger.exception(
                "❌ A2A call failed - error sending message to evaluated agent",
                extra={
                    "message": message[:100] + "..." if len(message) > 100 else message,
                    "context_id": context_id,
                    "agent_url": self._evaluated_agent_address,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return {"response": "", "error": str(e)}

    async def __aenter__(self) -> Self:
        await self._http_client.__aenter__()
        return await super().__aenter__()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await super().__aexit__(exc_type, exc_value, traceback)
        await self._http_client.__aexit__(exc_type, exc_value, traceback)
