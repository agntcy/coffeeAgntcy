# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
from agent_recruiter.common.logging import get_logger

from agntcy_app_sdk.semantic.a2a.protocol import A2AProtocol
from agntcy_app_sdk.app_sessions import AppContainer
from agntcy_app_sdk.factory import AgntcyFactory
from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.types import AgentCard
from dotenv import load_dotenv
from uvicorn import Config, Server

from agent_recruiter.server.agent_executor import RecruiterAgentExecutor

load_dotenv()

# Define A2A agent card
AGENT_CARD = AgentCard(
    name="RecruiterAgent",
    url="http://example.com",
    description="Main recruiter agent coordinating sub-agents and handling recruitment tasks.",
    version="1.0.0",
    capabilities={},
    skills=[],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    supports_authenticated_extended_card=False,
)

ENABLE_HTTP = os.getenv("ENABLE_HTTP", "true").lower() == "true"
MESSAGE_TRANSPORT = os.getenv("MESSAGE_TRANSPORT")
TRANSPORT_SERVER_ENDPOINT = os.getenv("TRANSPORT_SERVER_ENDPOINT")


logger = get_logger(__name__)

# Initialize a multi-protocol, multi-transport agntcy factory.
factory = AgntcyFactory("recruiter", enable_tracing=True)

async def run_http_server(server):
    """Run the HTTP/REST server."""
    try:
        config = Config(app=server.build(), host="0.0.0.0", port=8881, loop="asyncio")
        userver = Server(config)
        await userver.serve()
    except Exception as e:
        logger.error(f"HTTP server encountered an error: {e}")

async def run_transport(server, transport_type, endpoint):
    """Run the transport and broadcast bridge."""
    try:
        personal_topic = A2AProtocol.create_agent_topic(AGENT_CARD)
        transport = factory.create_transport(transport_type, endpoint=endpoint, name=f"default/default/{personal_topic}")

        # Create an application session with multiple containers
        app_session = factory.create_app_session()
        
        app_session.add_app_container("agent_server", AppContainer(
            server,
            transport=transport,
            topic=personal_topic,
        ))

        await app_session.start_session("agent_server")

    except Exception as e:
        logger.error(f"Transport encountered an error: {e}")
        await app_session.stop_all_sessions()

async def main():
    """
    Main entry point to start the server with specified transports.
    """
    request_handler = DefaultRequestHandler(
        agent_executor=RecruiterAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=AGENT_CARD, http_handler=request_handler
    )

    # Check if MESSAGE_TRANSPORT and TRANSPORT_SERVER_ENDPOINT are set
    if not MESSAGE_TRANSPORT or not TRANSPORT_SERVER_ENDPOINT:
        logger.warning("MESSAGE_TRANSPORT or TRANSPORT_SERVER_ENDPOINT not set. Fallback to http only.")
        ENABLE_HTTP = True

    # Run HTTP server and transport logic concurrently
    tasks = []
    if ENABLE_HTTP:
        tasks.append(asyncio.create_task(run_http_server(server)))

    if MESSAGE_TRANSPORT and TRANSPORT_SERVER_ENDPOINT:
        tasks.append(asyncio.create_task(run_transport(server, MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT)))
    
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully on keyboard interrupt.")
    except Exception as e:
        print(f"Error occurred: {e}")