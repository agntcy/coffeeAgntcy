# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared plumbing for the Grandma Helper agents.

Every helper agent is a small A2A server that takes one JSON object and
returns one JSON object. This module holds the parts they all share: the
agent card, the A2A executor, serving on SLIM/NATS/HTTP, and the LLM call.
"""

import json
import logging
import os
from collections.abc import Awaitable, Callable
from uuid import uuid4

import config.config
import litellm
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    InternalError,
    Message,
    Part,
    Role,
    Task,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.semantic.a2a.transport_types import normalize_transport
from config.config import LLM_MODEL, OTEL_SDK_DISABLED
from opentelemetry import trace

logger = logging.getLogger("helper.common")

Handler = Callable[[dict], Awaitable[dict]]

tracer = trace.get_tracer("helper.agents")


def make_card(
    agent_id: str, name: str, description: str, examples: list[str], port: int
) -> AgentCard:
    """Agent card reachable over SLIM (preferred), NATS and HTTP JSON-RPC."""
    slim_url = f"slim://{config.config.SLIM_SERVER}/helper/agents/{agent_id}"
    return AgentCard(
        name=name,
        description=description,
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id=agent_id,
                name=name,
                description=description,
                tags=["helper", "elderly", "mongolian"],
                examples=examples,
            )
        ],
        supportsAuthenticatedExtendedCard=False,
        preferred_transport="slim",
        url=slim_url,
        additional_interfaces=[
            AgentInterface(transport="slim", url=slim_url),
            AgentInterface(
                transport="nats",
                url=f"nats://{config.config.NATS_SERVER}/helper/agents/{agent_id}",
            ),
            AgentInterface(
                transport="jsonrpc",
                url=f"http://0.0.0.0:{os.getenv('AGENT_PORT', port)}",
            ),
        ],
    )


class JsonAgentExecutor(AgentExecutor):
    """Runs ``handler`` on the JSON object in the request and replies with JSON."""

    def __init__(self, card: AgentCard, handler: Handler):
        self.card = card
        self.handler = handler

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        text = context.get_user_input()
        try:
            request = json.loads(text)
        except json.JSONDecodeError:
            # Plain text is accepted too, as {"text": ...}.
            request = {"text": text}
        # One span per request, holding what the agent was asked and what it
        # answered, so each agent's opinion is visible in the trace.
        with tracer.start_as_current_span(f"{self.card.skills[0].id}.handle") as span:
            span.set_attribute("helper.input", text)
            try:
                result = await self.handler(request)
            except Exception as e:
                logger.exception("%s failed", self.card.name)
                span.record_exception(e)
                raise ServerError(error=InternalError()) from e
            span.set_attribute("helper.output", json.dumps(result, ensure_ascii=False))
        await event_queue.enqueue_event(
            Message(
                message_id=str(uuid4()),
                role=Role.agent,
                metadata={"name": self.card.name},
                parts=[Part(TextPart(text=json.dumps(result, ensure_ascii=False)))],
            )
        )

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())


async def serve(card: AgentCard, handler: Handler) -> None:
    """Serve the agent on every transport in its card until interrupted.

    Same approach as the Lungo agents: each transport runs in its own session,
    and only a failure of the preferred one (SLIM) is fatal.
    """
    factory = AgntcyFactory(
        f"helper.{card.skills[0].id}", enable_tracing=not OTEL_SDK_DISABLED
    )
    request_handler = DefaultRequestHandler(
        agent_executor=JsonAgentExecutor(card, handler),
        task_store=InMemoryTaskStore(),
    )
    preferred = normalize_transport(card.preferred_transport or "")
    advertised = {normalize_transport(i.transport) for i in card.additional_interfaces}

    started = []
    for interface in card.additional_interfaces:
        transport = normalize_transport(interface.transport)
        session = factory.create_app_session()
        builder = session.add_a2a_card(card, request_handler).with_factory(factory)
        for other in advertised - {transport}:
            builder = builder.skip(other)
        try:
            await builder.start(keep_alive=False)
        except Exception as exc:
            if transport == preferred:
                raise
            logger.error("Transport %r failed to start: %s", interface.transport, exc)
            continue
        started.append(session)
        logger.info("Serving %s on %s", interface.transport, interface.url)

    if not started:
        raise RuntimeError(f"{card.name}: no transport could be started")
    logger.info("%s ready", card.name)
    await started[0].start_all_sessions(keep_alive=True)


# Each agent can use its own model (HELPER_LLM_MODEL). Spreading agents
# across models also spreads them across the provider's per-model limits.
MODEL = os.getenv("HELPER_LLM_MODEL") or LLM_MODEL

# Answers to identical prompts are reused: repeat questions are instant,
# cost no rate limit, and always get the same answer.
_CACHE: dict[tuple[str, str, bool], str] = {}
_CACHE_SIZE = 256


async def llm(system: str, user: str, *, as_json: bool = False) -> str | dict:
    """One LLM call. With ``as_json`` the reply is parsed as a JSON object."""
    key = (system, user, as_json)
    content = _CACHE.get(key)
    if content is None:
        kwargs = {"response_format": {"type": "json_object"}} if as_json else {}
        if "gpt-oss" in MODEL:
            # Short reasoning keeps replies fast and inside free-tier limits.
            kwargs["reasoning_effort"] = "low"
        response = await litellm.acompletion(
            model=MODEL,
            temperature=0.1,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            # Back off and retry when the provider says "too many requests".
            num_retries=3,
            **kwargs,
        )
        content = response.choices[0].message.content.strip()
        if len(_CACHE) >= _CACHE_SIZE:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[key] = content
    return json.loads(content) if as_json else content
