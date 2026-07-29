# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging

import config.logging_config  # noqa: F401 - runs setup on import; must be first

logger = logging.getLogger(__name__)

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from agents.farms.brazil.agent_executor import FarmAgentExecutor
from agents.farms.brazil.card import AGENT_CARD
from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.semantic.a2a.transport_types import normalize_transport
from config.config import OTEL_SDK_DISABLED
from dotenv import load_dotenv

load_dotenv()

# Initialize a multi-protocol, multi-transport agntcy factory.
factory = AgntcyFactory("lungo.brazil_farm", enable_tracing=not OTEL_SDK_DISABLED)


async def serve_all_a2a_interfaces(
    request_handler: DefaultRequestHandler,
    agent_card: AgentCard,
):
    """Serve the Brazil Coffee Farm agent across all A2A transports defined in its AgentCard.

    Each advertised interface is started in its own session so a broker that is
    unavailable at startup (e.g. NATS) cannot abort the others. A startup failure
    on the card's ``preferred_transport`` is fatal; failures on any other transport
    are logged and skipped so the agent still comes up on the transports that are
    healthy.
    The card's ``additional_interfaces`` typically include:
    - **slimrpc** - point-to-point transport for direct client-agent communication
    - **slim** - SLIM-based group messaging and pub/sub transport
    - **nats** - NATS-based pub/sub transport for broadcasting to multiple subscribers
    - **jsonrpc** - JSON-RPC endpoint for direct client-agent communication over HTTP

    The card's ``preferred_transport`` determines the primary ``url`` advertised
    to callers.  The session is kept alive until the process is interrupted.

    Args:
        request_handler: The A2A request handler wired to the
            :class:`FarmAgentExecutor` and an in-memory task store.
        agent_card: The ``AgentCard`` describing this agent's capabilities,
            skills, and transport interfaces.
    """
    interfaces = agent_card.additional_interfaces or []
    if not interfaces:
        raise ValueError("agent_card.additional_interfaces is empty; nothing to serve")

    preferred = normalize_transport(agent_card.preferred_transport or "")
    advertised = {normalize_transport(i.transport) for i in interfaces}
    if preferred and preferred not in advertised:
        logger.warning(
            "preferred_transport %r is not advertised in additional_interfaces %s; "
            "no transport will be treated as required at startup",
            agent_card.preferred_transport,
            sorted(advertised),
        )

    started = []
    for interface in interfaces:
        transport = normalize_transport(interface.transport)
        is_preferred = bool(preferred) and transport == preferred

        # Serve only this interface in its own session; skipping the other
        # advertised transports keeps a single failing transport isolated.
        session = factory.create_app_session()
        builder = session.add_a2a_card(agent_card, request_handler).with_factory(
            factory
        )
        for other in advertised - {transport}:
            builder = builder.skip(other)

        try:
            await builder.start(keep_alive=False)
        except Exception as exc:
            if is_preferred:
                logger.error(
                    "Preferred transport %r failed to start; shutting down: %s",
                    interface.transport,
                    exc,
                )
                raise
            logger.error(
                "Transport %r failed to start; continuing without it: %s",
                interface.transport,
                exc,
            )
            continue

        started.append(session)
        logger.info("Serving %s on %s", interface.transport, interface.url)

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
    )

    await serve_all_a2a_interfaces(request_handler, AGENT_CARD)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully on keyboard interrupt.")
    except Exception as e:
        print(f"Error occurred: {e}")
