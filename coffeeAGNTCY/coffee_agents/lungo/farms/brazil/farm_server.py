# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio

from agntcy_app_sdk.factory import GatewayFactory

from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
import os


from agent_executor import FarmAgentExecutor
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT, 
    TRANSPORT_SERVER_ENDPOINT,
    FARM_BROADCAST_TOPIC,
)
from card import AGENT_CARD
from ioa_observe.sdk import Observe
from ioa_observe.sdk.instrumentations.a2a import A2AInstrumentor
from ioa_observe.sdk.instrumentations.slim import SLIMInstrumentor
from dotenv import load_dotenv
load_dotenv()
Observe.init("lungo_brazil_farm", api_endpoint=os.getenv("OTLP_HTTP_ENDPOINT"))

SLIMInstrumentor().instrument()


# Initialize a multi-protocol, multi-transport gateway factory.
factory = GatewayFactory()

async def main():
    """Run the A2A server with the Farm Agent."""

    request_handler = DefaultRequestHandler(
        agent_executor=FarmAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=AGENT_CARD, http_handler=request_handler
    )

    transport = factory.create_transport(
        DEFAULT_MESSAGE_TRANSPORT,
        endpoint=TRANSPORT_SERVER_ENDPOINT,
    )

    # explicitly create a broadcast bridge to the farm yield topic
    broadcast_bridge = factory.create_bridge(
        server, transport=transport, topic=FARM_BROADCAST_TOPIC
    )

    # create the default bridge to the server with a topic generated from the agent card
    bridge = factory.create_bridge(server, transport=transport) 

    await broadcast_bridge.start(blocking=False)
    await bridge.start(blocking=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully on keyboard interrupt.")
    except Exception as e:
        print(f"Error occurred: {e}")