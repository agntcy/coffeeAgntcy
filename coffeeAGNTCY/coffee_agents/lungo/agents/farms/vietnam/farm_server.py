# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio

from agntcy_app_sdk.semantic.a2a.protocol import A2AProtocol
from agntcy_app_sdk.app_sessions import AppContainer
from agntcy_app_sdk.factory import AgntcyFactory
from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from dotenv import load_dotenv
from uvicorn import Config, Server

from agents.farms.vietnam.agent_executor import FarmAgentExecutor
from agents.farms.vietnam.card import AGENT_CARD
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT,
    TRANSPORT_SERVER_ENDPOINT,
    FARM_BROADCAST_TOPIC,
    ENABLE_HTTP,
)

load_dotenv()

# Initialize a multi-protocol, multi-transport agntcy factory.
factory = AgntcyFactory("lungo.vietnam_farm", enable_tracing=True)

async def run_http_server(server):
    """Run the HTTP/REST server."""
    try:
        config = Config(app=server.build(), host="0.0.0.0", port=9997, loop="asyncio")
        userver = Server(config)
        await userver.serve()
    except Exception as e:
        print(f"HTTP server encountered an error: {e}")

async def run_transport(server, transport_type, endpoint):
    """Run the transport and broadcast bridge."""
    try:
        personal_topic = A2AProtocol.create_agent_topic(AGENT_CARD)
        transport = factory.create_transport(transport_type, endpoint=endpoint, name=f"default/default/{personal_topic}")

        # Create an application session with multiple containers
        app_session = factory.create_app_session(max_sessions=2)
        
        # Add containers for broadcast and personal topics
        app_session.add_app_container("public_session", AppContainer(
            server,
            transport=transport,
            topic=FARM_BROADCAST_TOPIC,
        ))
        app_session.add_app_container("private_session", AppContainer(
            server,
            transport=transport,
            topic=personal_topic,
        ))

        await app_session.start_session("public_session")
        await app_session.start_session("private_session")

    except Exception as e:
        print(f"Transport encountered an error: {e}")
        await app_session.stop_all_sessions()

async def main(enable_http: bool):
    """Run the A2A server with both HTTP and transport logic."""
    request_handler = DefaultRequestHandler(
        agent_executor=FarmAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=AGENT_CARD, http_handler=request_handler
    )

    # Run HTTP server and transport logic concurrently
    tasks = []
    if enable_http:
        tasks.append(asyncio.create_task(run_http_server(server)))
    tasks.append(asyncio.create_task(run_transport(server, DEFAULT_MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT)))
    
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    try:
        asyncio.run(main(ENABLE_HTTP))
    except KeyboardInterrupt:
        print("\nShutting down gracefully on keyboard interrupt.")
    except Exception as e:
        print(f"Error occurred: {e}")