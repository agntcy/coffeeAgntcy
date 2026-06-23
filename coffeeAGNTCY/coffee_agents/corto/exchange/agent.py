# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
from uuid import uuid4

from a2a.types import Message, Part, Role, TextPart
from agntcy_app_sdk.semantic.a2a.client.factory import A2AClientFactory
from common.a2a_transport_config import build_a2a_client_config
from common.llm import get_llm
from exchange.errors import (
    RemoteAgentNoResponseError,
    TransportTimeoutError,
    _is_no_payload_error,
    _is_timeout_error,
)
from farm.card import AGENT_CARD as farm_agent_card
from ioa_observe.sdk.decorators import agent
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger("corto.exchange.agent")

a2a_client_factory = A2AClientFactory(
    build_a2a_client_config(
        namespace="default",
        group="default",
        agent_name="exchange",
    )
)

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
                        "description": "The user prompt to process",
                    }
                },
                "required": ["prompt"],
            },
        },
    }
]

system_prompt = (
    "You are an assistant that checks if the user prompt is relevant to coffee flavor, taste or sensory profile. "
    "If relevant, call the a2a_client_send_message with the prompt. Otherwise, respond with 'I'm sorry, I cannot assist with that request. Please ask about coffee flavor or taste.'"
)

_A2A_MAX_ATTEMPTS = 5
_A2A_BACKOFF_BASE = 3


def _build_message(prompt: str) -> Message:
    return Message(
        messageId=str(uuid4()),
        role=Role.user,
        parts=[Part(root=TextPart(text=prompt))],
    )


def _extract_text_from_events(events: list) -> str | None:
    result_text = None
    for event in events:
        if isinstance(event, Message):
            for part in event.parts:
                if hasattr(part.root, "text"):
                    result_text = part.root.text
        elif isinstance(event, tuple):
            task, _update = event
            if hasattr(task, "status") and task.status and task.status.message:
                for part in task.status.message.parts:
                    if hasattr(part.root, "text"):
                        result_text = part.root.text
    return result_text


async def _send_a2a_with_retry(client, message: Message):
    for attempt in range(_A2A_MAX_ATTEMPTS):
        try:
            events = []
            async for event in client.send_message(message):
                events.append(event)

            if events:
                return events

            raise RemoteAgentNoResponseError(
                "Remote agent returned no response (missing or invalid payload).",
                cause=None,
            )
        except RemoteAgentNoResponseError:
            raise
        except Exception as e:
            if not _is_timeout_error(e):
                if _is_no_payload_error(e):
                    raise RemoteAgentNoResponseError(
                        "Remote agent returned no response (missing or invalid payload).",
                        cause=e,
                    ) from e
                logger.error("A2A send_message failed: %s", e)
                raise
            if attempt < _A2A_MAX_ATTEMPTS - 1:
                delay = _A2A_BACKOFF_BASE**attempt
                logger.warning(
                    "A2A request timed out, retrying (attempt %s/%s) after %ss.",
                    attempt + 2,
                    _A2A_MAX_ATTEMPTS,
                    delay,
                )
                await asyncio.sleep(delay)
                continue
            raise TransportTimeoutError(
                "Remote agent did not respond in time (SLIM receive timeout).",
                cause=e,
            ) from e


@agent(name="exchange_agent")
class ExchangeAgent:
    async def execute_agent_with_llm(self, user_prompt: str):
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = get_llm().invoke(messages, tools=tools)

        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call["name"] == "a2a_client_send_message":
                    return await self.a2a_client_send_message(
                        tool_call["args"]["prompt"]
                    )
        return response.content

    async def a2a_client_send_message(self, prompt: str):
        client = await a2a_client_factory.create(farm_agent_card)
        events = await _send_a2a_with_retry(client, _build_message(prompt))
        text = _extract_text_from_events(events)
        if text is None:
            raise RemoteAgentNoResponseError(
                "Remote agent returned no response (missing or invalid payload).",
                cause=None,
            )
        return text
