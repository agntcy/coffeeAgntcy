# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from agntcy_app_sdk.factory import AgntcyFactory
from config.config import DEFAULT_MESSAGE_TRANSPORT, FARM_AGENT_HOST, FARM_AGENT_PORT
from dotenv import load_dotenv
from farm.agent_executor import FarmAgentExecutor
from farm.card import AGENT_CARD
from uvicorn import Config, Server

load_dotenv()

logger = logging.getLogger("corto.farm.server")
factory = AgntcyFactory("corto.farm_agent", enable_tracing=True)


async def serve_slim(agent_card, request_handler):
    session = factory.create_app_session()
    await session.add_a2a_card(agent_card, request_handler).start(keep_alive=False)
    logger.info("Agent ready")
    await session.start_all_sessions(keep_alive=True)


async def main():
    request_handler = DefaultRequestHandler(
        agent_executor=FarmAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(
        agent_card=AGENT_CARD, http_handler=request_handler
    )

    if DEFAULT_MESSAGE_TRANSPORT == "A2A":
        config = Config(
            app=server.build(),
            host=FARM_AGENT_HOST,
            port=FARM_AGENT_PORT,
            loop="asyncio",
        )
        await Server(config).serve()
    else:
        await serve_slim(AGENT_CARD, request_handler)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully on keyboard interrupt.")
    except Exception as e:
        logger.error("Error occurred: %s", e)
        raise
