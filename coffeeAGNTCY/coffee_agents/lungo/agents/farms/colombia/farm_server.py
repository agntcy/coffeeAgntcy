# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import config.logging_config  # noqa: F401 - runs setup on import; must be first

import asyncio

from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from a2a.server.request_handlers import DefaultRequestHandler

from agntcy_app_sdk.factory import AgntcyFactory

from agents.farms.colombia.agent_executor import FarmAgentExecutor
from agents.farms.colombia.card import AGENT_CARD

from dotenv import load_dotenv

load_dotenv()

# Initialize a multi-protocol, multi-transport agntcy factory.
factory = AgntcyFactory("lungo.colombia_farm", enable_tracing=True)


async def serve_all_a2a_interfaces(
    request_handler: DefaultRequestHandler, 
    agent_card: AgentCard,
):
    """Serve the Colombia Coffee Farm agent across all A2A transports defined in its AgentCard.

    Creates an AgntcyFactory application session and registers every transport
    interface declared in the card's ``additional_interfaces``, which include:

    - **slimrpc** – point-to-point transport for direct client-agent communication
    - **slim** – SLIM-based group communication and pub/sub transport
    - **nats** – NATS-based pub/sub transport for broadcasting to multiple subscribers
    - **jsonrpc** – JSON-RPC endpoint for direct client-agent communication over HTTP

    The card's ``preferred_transport`` determines the primary ``url`` advertised
    to callers.  The session is kept alive until the process is interrupted.

    Args:
        request_handler: The A2A request handler wired to the
            :class:`FarmAgentExecutor` and an in-memory task store.
        agent_card: The ``AgentCard`` describing this agent's capabilities,
            skills, and transport interfaces.
    """

    session = factory.create_app_session()

    await session.add_a2a_card(agent_card, request_handler).start(keep_alive=True)

async def main():
    """Main entry point for multi-pattern, multi-transport serving."""
    request_handler = DefaultRequestHandler(
        agent_executor=FarmAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    await serve_all_a2a_interfaces(request_handler, AGENT_CARD)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully on keyboard interrupt.")
    except Exception as e:
        print(f"Error occurred: {e}")
