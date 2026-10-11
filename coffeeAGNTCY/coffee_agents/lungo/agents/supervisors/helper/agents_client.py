# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Calls the helper agents over A2A (SLIM by default)."""

import asyncio
import copy
import json
import logging
import os
from uuid import uuid4

from a2a.types import AgentCard, Message, Part, Role, TextPart
from agntcy_app_sdk.semantic.a2a.client.factory import A2AClientFactory
from common.a2a_transport_config import build_a2a_client_config
from config.config import DEFAULT_MESSAGE_TRANSPORT

logger = logging.getLogger("helper.supervisor.client")

# The SLIM transport can wait forever on an agent that has gone away, so
# every call gets its own deadline and a missing agent counts as down.
AGENT_DEADLINE_SECONDS = float(os.getenv("HELPER_AGENT_DEADLINE_SECONDS", "15"))

_factory: A2AClientFactory | None = None


def _client_factory() -> A2AClientFactory:
    global _factory
    if _factory is None:
        _factory = A2AClientFactory(
            build_a2a_client_config(
                namespace="helper",
                group="agents",
                agent_name="helper_supervisor",
                include_nats=True,
            )
        )
    return _factory


class AgentUnavailable(Exception):
    """The agent did not answer in time or its answer was unusable."""


def _reply_text(events: list) -> str | None:
    text = None
    for event in events:
        message = event if isinstance(event, Message) else None
        if isinstance(event, tuple):
            task = event[0]
            status = getattr(task, "status", None)
            message = getattr(status, "message", None)
        for part in getattr(message, "parts", None) or []:
            if hasattr(part.root, "text"):
                text = part.root.text
    return text


async def _call(card: AgentCard, payload: dict) -> dict:
    card = copy.deepcopy(card)
    card.preferred_transport = DEFAULT_MESSAGE_TRANSPORT.lower()
    client = await _client_factory().create(card)
    message = Message(
        messageId=str(uuid4()),
        role=Role.user,
        parts=[Part(TextPart(text=json.dumps(payload, ensure_ascii=False)))],
    )
    events = [event async for event in client.send_message(message)]
    text = _reply_text(events)
    if not text:
        raise AgentUnavailable(f"{card.name} returned nothing")
    return json.loads(text)


async def call_agent(card: AgentCard, payload: dict) -> dict:
    """Send ``payload`` to the agent and return its JSON reply.

    Raises:
        AgentUnavailable: on timeout, transport error, or an unreadable reply.
    """
    try:
        return await asyncio.wait_for(_call(card, payload), AGENT_DEADLINE_SECONDS)
    except TimeoutError as e:
        logger.warning(
            "%s did not answer within %ss", card.name, AGENT_DEADLINE_SECONDS
        )
        raise AgentUnavailable(f"{card.name} did not answer in time") from e
    except AgentUnavailable:
        raise
    except Exception as e:
        logger.warning("%s failed: %s", card.name, e)
        raise AgentUnavailable(f"{card.name} failed") from e
