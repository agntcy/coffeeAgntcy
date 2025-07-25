# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
from uvicorn import Config, Server
from starlette.routing import Route
from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from agent_executor import FarmAgentExecutor
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT,
    TRANSPORT_SERVER_ENDPOINT,
    FARM_BROADCAST_TOPIC,
    ENABLE_HTTP,
)
from card import AGENT_CARD
from agent import factory
from dotenv import load_dotenv
from utils import create_badge_for_colombia_farm

load_dotenv()

class CustomA2AStarletteApplication(A2AStarletteApplication):
    def routes(
            self,
            agent_card_url: str = '/.well-known/agent.json',
            extended_agent_card_url: str = '/agent/authenticatedExtendedCard',
            rpc_url: str = '/',
    ) -> list[Route]:
        """Extend the routes to include custom endpoints."""
        return super().routes(agent_card_url, extended_agent_card_url, rpc_url)

async def run_http_server(server):
    """Run the HTTP/REST server."""
    try:
        config = Config(app=server.build(), host="0.0.0.0", port=9998, loop="asyncio")
        userver = Server(config)
        await userver.serve()
    except Exception as e:
        print(f"HTTP server encountered an error: {e}")

async def run_transport(server, transport_type, endpoint, block):
    """Run the transport and broadcast bridge."""
    try:
        transport = factory.create_transport(transport_type, endpoint=endpoint)

        # Create a broadcast bridge to the farm yield topic
        broadcast_bridge = factory.create_bridge(
            server, transport=transport, topic=FARM_BROADCAST_TOPIC
        )

        # Create the default bridge to the server
        bridge = factory.create_bridge(server, transport=transport)

        await broadcast_bridge.start(blocking=False)
        await bridge.start(blocking=block)
    except Exception as e:
        print(f"Transport encountered an error: {e}")

async def main(enable_http: bool):
    """Run the A2A server with both HTTP and transport logic."""
    request_handler = DefaultRequestHandler(
        agent_executor=FarmAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = CustomA2AStarletteApplication(
        agent_card=AGENT_CARD, http_handler=request_handler
    )

    # Run HTTP server and transport logic concurrently
    tasks = []
    if enable_http:
        tasks.append(asyncio.create_task(run_http_server(server)))
        tasks.append(asyncio.create_task(create_badge_for_colombia_farm()))
    tasks.append(asyncio.create_task(run_transport(server, DEFAULT_MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT, block=True)))

    await asyncio.gather(*tasks)

if __name__ == '__main__':
    try:
        asyncio.run(main(ENABLE_HTTP))
    except KeyboardInterrupt:
        print("\nShutting down gracefully on keyboard interrupt.")
    except Exception as e:
        print(f"Error occurred: {e}")
