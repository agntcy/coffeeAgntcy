# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from uuid import uuid4

from ioa_observe.sdk.decorators import agent
from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.semantic.a2a.protocol import A2AProtocol
from config.config import DEFAULT_MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT
from langchain_core.messages import HumanMessage, SystemMessage
from common.llm import get_llm
from a2a.types import (
    SendMessageRequest,
    MessageSendParams,
    Message,
    Part,
    TextPart,
    Role,
)

from exchange.errors import (
    TransportTimeoutError,
    RemoteAgentNoResponseError,
    _is_timeout_error,
    _is_no_payload_error,
)
from farm.card import AGENT_CARD as farm_agent_card

logger = logging.getLogger("corto.exchange.agent")

tools = [
    {
        "type": "function",
        "function": {
            "name": "a2a_client_send_message",
            "description": "Processes relevant user prompts and returns a response",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The user prompt to process"
                    }
                },
                "required": ["prompt"]
            }
        }
    }
]

system_prompt = (
    "You are an assistant that checks if the user prompt is relevant to coffee flavor, taste or sensory profile. "
    "If relevant, call the a2a_client_send_message with the prompt. Otherwise, respond with 'I'm sorry, I cannot assist with that request. Please ask about coffee flavor or taste.'"
)


def _build_send_message_request(prompt: str) -> SendMessageRequest:
    return SendMessageRequest(
        id=str(uuid4()),
        params=MessageSendParams(
            message=Message(
                message_id=str(uuid4()),
                role=Role.user,
                parts=[Part(TextPart(text=prompt))],
            )
        ),
    )


def _parse_a2a_response(response):
    if response is None or getattr(response, "root", None) is None:
        raise RemoteAgentNoResponseError(
            "Remote agent returned no response (missing or invalid payload).",
            cause=None,
        )
    if response.root.result:
        if not response.root.result.parts:
            raise ValueError("No response parts found in the message.")
        part = response.root.result.parts[0].root
        if hasattr(part, "text"):
            return part.text
    elif response.root.error:
        raise Exception(f"A2A error: {response.root.error.message}")
    return None


async def _send_a2a_with_retry(client, request):
    try:
        response = await client.send_message(request)
        logger.info(f"Response received from A2A agent: {response}")
        return response
    except Exception as e:
        if not _is_timeout_error(e):
            if _is_no_payload_error(e):
                raise RemoteAgentNoResponseError(
                    "Remote agent returned no response (missing or invalid payload).",
                    cause=e,
                ) from e
            logger.error("A2A send_message failed: %s", e)
            raise
        logger.warning("A2A request timed out, retrying once.")
        try:
            response = await client.send_message(request)
            logger.info(f"Response received from A2A agent (retry): {response}")
            return response
        except Exception as e2:
            if _is_timeout_error(e2):
                raise TransportTimeoutError(
                    "Remote agent did not respond in time (SLIM receive timeout).",
                    cause=e2,
                ) from e2
            if _is_no_payload_error(e2):
                raise RemoteAgentNoResponseError(
                    "Remote agent returned no response (missing or invalid payload).",
                    cause=e2,
                ) from e2
            logger.error("A2A send_message failed after retry: %s", e2)
            raise


@agent(name="exchange_agent")
class ExchangeAgent:
    def __init__(self, factory: AgntcyFactory):
        self.factory = factory

    async def execute_agent_with_llm(self, user_prompt: str):
        """
        Processes a user prompt using the LLM to determine if the prompt is relevant to coffee flavor, taste or sensory profile.
        If relevant, calls the a2a_client_send_message with the prompt. Otherwise, responds with 'I'm sorry, I cannot assist with that request. Please ask about coffee flavor or taste.'

        Args:
            user_prompt (str): The user prompt to process.

        Returns:
            str: The response from the LLM or the tool if called.
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        # Invoke LLM WITHOUT binding - pass tools directly in kwargs
        response = get_llm().invoke(messages, tools=tools)

        # Check if tool was called
        if hasattr(response, 'tool_calls') and response.tool_calls:
            logger.info("Tool was called!")
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                logger.info(f"Tool: {tool_name}")
                logger.info(f"Arguments: {tool_args}")

                # Manual local routing to the tool
                if tool_name == "a2a_client_send_message":
                    result = await self.a2a_client_send_message(tool_args["prompt"])
                    logger.info(f"Tool Result: {result}")
                    return result
        else:
            logger.info("No tool called - LLM responded directly")
            return response.content

    async def a2a_client_send_message(self, prompt: str):
        """
        Send the user-provided prompt to the farm agent over A2A transport and
        return the resulting response payload.

        Args:
            prompt (str): Plain-text prompt to forward to the farm agent.

        Returns:
            Any: Whatever payload is returned by `client.send_message`.

        Raises:
            TransportTimeoutError: When the request times out after retry.
            RemoteAgentNoResponseError: When the remote returns no usable response (e.g. missing/invalid payload).
            Other exceptions (e.g. ValueError, ConnectionError) propagated as-is.
        """
        factory = self.factory
        a2a_topic = A2AProtocol.create_agent_topic(farm_agent_card)
        transport = factory.create_transport(
            DEFAULT_MESSAGE_TRANSPORT,
            endpoint=TRANSPORT_SERVER_ENDPOINT,
            name="default/default/exchange"  # SLIM transport requires a routable name (org/namespace/agent) to build the PyName used for request-reply routing
        )
        client = await factory.create_client(
            "A2A",
            agent_topic=a2a_topic,
            transport=transport,
        )
        request = _build_send_message_request(prompt)
        response = await _send_a2a_with_retry(client, request)
        return _parse_a2a_response(response)

