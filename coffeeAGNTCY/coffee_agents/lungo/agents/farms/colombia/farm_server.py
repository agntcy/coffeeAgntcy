# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
from uvicorn import Config, Server
from starlette.routing import Route
from a2a.server.apps import A2AStarletteApplication
from agntcy_app_sdk.protocols.a2a.protocol import A2AProtocol
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
        personal_topic = A2AProtocol.create_agent_topic(AGENT_CARD)
        transport = factory.create_transport(transport_type, endpoint=endpoint, name=f"default/default/{personal_topic}")

        broadcast_bridge = factory.create_bridge(
            server, transport=transport, topic=FARM_BROADCAST_TOPIC
        )
        private_bridge = factory.create_bridge(server, transport=transport, topic=personal_topic)
        
        await broadcast_bridge.start(blocking=False)
        await private_bridge.start(blocking=block)

    except Exception as e:
        print(f"Transport encountered an error: {e}")

async def main(enable_http: bool):
    """Run the A2A server with both HTTP and transport logic."""
    request_handler = DefaultRequestHandler(
        agent_executor=FarmAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=AGENT_CARD, http_handler=request_handler
    )

    # Run HTTP server and transport logic concurrently using TaskGroup
    async with asyncio.TaskGroup() as tg:
        if enable_http:
            tg.create_task(safe_run(run_http_server, server))
            tg.create_task(safe_run(create_badge_for_colombia_farm))
        tg.create_task(safe_run(run_transport, server, DEFAULT_MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT, block=True))

async def safe_run(coro, *args, **kwargs):
    """Run a coroutine safely, catching and logging exceptions."""
    try:
        await coro(*args, **kwargs)
    except asyncio.CancelledError:
        print(f"Task {coro.__name__} was cancelled.")
    except Exception as e:
        print(f"Task {coro.__name__} encountered an error: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main(ENABLE_HTTP))
    except KeyboardInterrupt:
        print("\nShutting down gracefully on keyboard interrupt.")
    except Exception as e:
        print(f"Error occurred: {e}")
