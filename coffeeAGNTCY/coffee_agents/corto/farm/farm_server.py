# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
from uvicorn import Config, Server

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv

from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.protocols.a2a.protocol import A2AProtocol

from config.config import FARM_AGENT_HOST, FARM_AGENT_PORT
from config.config import DEFAULT_MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT
from farm.agent_executor import FarmAgentExecutor
from farm.card import AGENT_CARD

load_dotenv()

# Initialize a multi-protocol, multi-transport gateway factory.
factory = AgntcyFactory("corto.farm_agent", enable_tracing=True)

async def main():
    """
    Starts the farm agent server using the specified transport mechanism.

    This function initializes a FarmAgentExecutor wrapped with a DefaultRequestHandler,
    and serves it using an A2AStarletteApplication. The agent is exposed via either:

    1. An HTTP server using native A2A (Agent-to-Agent) protocol via Starlette, or
    2. A bridge-based transport using the app-sdk factory (e.g., SLIM or other supported transports).

    The transport method is determined by the `DEFAULT_MESSAGE_TRANSPORT` environment variable.

    - If set to `"A2A"`, the agent is served via a local FastAPI/Starlette HTTP server.
    - Otherwise, it uses a pluggable transport layer (like SLIM) via the app-sdk factory, connecting to
    the server or gateway defined by `TRANSPORT_SERVER_ENDPOINT`.

    This design enables interchangeable transport layers for agent communication while keeping the
    agent logic transport-agnostic.

    Dependencies:
    - AGNTCY App SDK: https://github.com/agntcy/app-sdk

    Environment Variables:
    - DEFAULT_MESSAGE_TRANSPORT: Transport protocol name ("A2A", "slim", etc.)
    - TRANSPORT_SERVER_ENDPOINT: Endpoint for the external transport (if used)
    - FARM_AGENT_HOST / FARM_AGENT_PORT: Host and port for local HTTP server (if "A2A" is selected)
    """


    request_handler = DefaultRequestHandler(
        agent_executor=FarmAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=AGENT_CARD, http_handler=request_handler
    )

    if DEFAULT_MESSAGE_TRANSPORT == "A2A":
        config = Config(app=server.build(), host=FARM_AGENT_HOST, port=FARM_AGENT_PORT, loop="asyncio")
        userver = Server(config)
        await userver.serve()
    else:
        transport = factory.create_transport(
            DEFAULT_MESSAGE_TRANSPORT,
            endpoint=TRANSPORT_SERVER_ENDPOINT,
            # SLIM transport requires a routable name (org/namespace/agent) to build the PyName used for request-reply routing to match the a2a client topic
            name= "default/default/" + A2AProtocol.create_agent_topic(AGENT_CARD)
        )
        bridge = factory.create_bridge(server, transport=transport)
        await bridge.start(blocking=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully on keyboard interrupt.")
    except Exception as e:
        print(f"Error occurred: {e}")