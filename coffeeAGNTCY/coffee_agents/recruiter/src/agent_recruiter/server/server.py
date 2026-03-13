# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from agent_recruiter.common.logging import configure_logger, get_logger

configure_logger()

import asyncio
from agntcy_app_sdk.factory import AgntcyFactory
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from dotenv import load_dotenv

from agent_recruiter.server.agent_executor import RecruiterAgentExecutor
from agent_recruiter.server.card import AGENT_CARD

load_dotenv()


logger = get_logger(__name__)

# Initialize a multi-protocol, multi-transport agntcy factory.
factory = AgntcyFactory("recruiter", enable_tracing=False)


async def main():
    """
    Main entry point to start the server with specified transports.
    """
    request_handler = DefaultRequestHandler(
        agent_executor=RecruiterAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    session = factory.create_app_session()

    await session.add_a2a_card(AGENT_CARD, request_handler).start(keep_alive=True)

if __name__ == '__main__':
    logger.info("Starting RecruiterAgent server...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully on keyboard interrupt.")
    except Exception as e:
        logger.error(f"Error occurred: {e}")