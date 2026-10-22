# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging

import config.logging_config  # noqa: F401 - runs setup on import; must be first

logger = logging.getLogger(__name__)

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from agents.farms.vietnam.agent_executor import FarmAgentExecutor
from agents.farms.vietnam.card import AGENT_CARD
from agntcy_app_sdk import A2AServerConfig
from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.semantic.a2a.card_utils import clone_card
from agntcy_app_sdk.semantic.a2a.transport_types import normalize_transport
from common.slim_placeholder_secret import (
    apply_placeholder_secret_policy,
    start_builder,
)
from config.config import OTEL_SDK_DISABLED
from dotenv import load_dotenv

load_dotenv()

# Initialize a multi-protocol, multi-transport agntcy factory.
factory = AgntcyFactory("lungo.vietnam_farm", enable_tracing=not OTEL_SDK_DISABLED)


async def serve_all_a2a_interfaces(
    request_handler: DefaultRequestHandler,
    agent_card: AgentCard,
):
    """Serve the Vietnam Coffee Farm agent across all A2A transports defined in its AgentCard.

    Each advertised interface is started in its own session so a broker that is
    unavailable at startup (e.g. NATS) cannot abort the others. A startup failure
    on the preferred transport (the first entry of ``supported_interfaces``) is
    fatal; failures on any other transport are logged and skipped so the agent
    still comes up on the transports that are healthy.
    The card's ``supported_interfaces`` typically include:
    - **slimpatterns** - SLIM-based group messaging and pub/sub transport
    - **natspatterns** - NATS-based pub/sub transport for broadcasting to multiple subscribers
    - **jsonrpc** - JSON-RPC endpoint for direct client-agent communication over HTTP

    The HTTP JSON-RPC endpoint also accepts A2A v0.3 requests (``message/send``,
    ``message/stream``) so v0.3 callers such as the recruiter interviewer keep
    working. The session is kept alive until the process is interrupted.

    Args:
        request_handler: The A2A request handler wired to the
            :class:`FarmAgentExecutor` and an in-memory task store.
        agent_card: The ``AgentCard`` describing this agent's capabilities,
            skills, and transport interfaces, ordered by preference.
    """
    interfaces = list(agent_card.supported_interfaces)
    if not interfaces:
        raise ValueError("agent_card.supported_interfaces is empty; nothing to serve")

    preferred = normalize_transport(interfaces[0].protocol_binding)
    advertised = {normalize_transport(i.protocol_binding) for i in interfaces}

    started = []
    for interface in interfaces:
        transport = normalize_transport(interface.protocol_binding)
        is_preferred = transport == preferred

        # Serve only this interface in its own session; skipping the other
        # advertised transports keeps a single failing transport isolated.
        session = factory.create_app_session()
        builder = apply_placeholder_secret_policy(
            session.add_a2a_card(agent_card, request_handler).with_factory(factory)
        )
        for other in advertised - {transport}:
            builder = builder.skip(other)
        if transport == "jsonrpc":
            # The override gets its own copy: with identity auth on, the SDK
            # edits the card it serves, which must not be the module card.
            builder = builder.override(
                "jsonrpc",
                A2AServerConfig(
                    agent_card=clone_card(agent_card),
                    request_handler=request_handler,
                    enable_v0_3_compat=True,
                ),
            )

        try:
            await start_builder(builder, keep_alive=False)
        except Exception as exc:
            if is_preferred:
                raise
            logger.error(
                "Transport %r failed to start; continuing without it: %s",
                interface.protocol_binding,
                exc,
            )
            continue

        started.append(session)
        logger.info("Serving %s on %s", interface.protocol_binding, interface.url)

    if not started:
        raise RuntimeError("No transport interfaces could be started")

    logger.info("Agent ready")

    # Keep the process alive; reuse a live session's keep-alive loop so
    # signal-based graceful shutdown continues to work.
    await started[0].start_all_sessions(keep_alive=True)


async def main():
    """Main entry point for multi-pattern, multi-transport serving."""
    request_handler = DefaultRequestHandler(
        agent_executor=FarmAgentExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=AGENT_CARD,
    )

    await serve_all_a2a_interfaces(request_handler, AGENT_CARD)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully on keyboard interrupt.")
    except Exception as e:
        logger.error("Error occurred: %s", e)
        raise SystemExit(1) from e
