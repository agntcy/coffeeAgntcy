# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from agntcy_app_sdk import A2AServerConfig
from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.semantic.a2a.transport_types import normalize_transport
from common.slim_placeholder_secret import (
    apply_placeholder_secret_policy,
    start_builder,
)
from config.config import DEFAULT_MESSAGE_TRANSPORT, FARM_AGENT_HOST, FARM_AGENT_PORT
from dotenv import load_dotenv
from farm.agent_executor import FarmAgentExecutor
from farm.card import AGENT_CARD
from uvicorn import Config, Server

load_dotenv()

logger = logging.getLogger("corto.farm.server")
factory = AgntcyFactory("corto.farm_agent", enable_tracing=True)


async def serve_multi_transport(agent_card, request_handler):
    """Serve the agent on every transport advertised in its AgentCard.

    Each advertised interface is started in its own session so a broker that
    is unavailable at startup (e.g. NATS) cannot abort the others. A startup
    failure on the preferred transport (the first entry of
    ``supported_interfaces``) is fatal; failures on any other transport are
    logged and skipped so the agent still comes up on the transports that are
    healthy.
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
    request_handler = DefaultRequestHandler(
        agent_executor=FarmAgentExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=AGENT_CARD,
    )

    if DEFAULT_MESSAGE_TRANSPORT == "A2A":
        server = A2AServerConfig(agent_card=AGENT_CARD, request_handler=request_handler)
        config = Config(
            app=server.build_app(),
            host=FARM_AGENT_HOST,
            port=FARM_AGENT_PORT,
            loop="asyncio",
        )
        await Server(config).serve()
    else:
        await serve_multi_transport(AGENT_CARD, request_handler)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully on keyboard interrupt.")
    except Exception as e:
        logger.error("Error occurred: %s", e)
        raise SystemExit(1) from e
