from uvicorn import Config, Server
import asyncio

from gateway_sdk.factory import GatewayFactory

from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler

from agent_executor import FarmAgentExecutor
from config.config import FARM_AGENT_HOST, FARM_AGENT_PORT
from config.config import DEFAULT_MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT
from card import AGENT_CARD

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

    if DEFAULT_MESSAGE_TRANSPORT == "A2A":
        config = Config(app=server.build(), host=FARM_AGENT_HOST, port=FARM_AGENT_PORT, loop="asyncio")
        userver = Server(config)
        await userver.serve()
    else:
        transport = factory.create_transport(
            DEFAULT_MESSAGE_TRANSPORT,
            endpoint=TRANSPORT_SERVER_ENDPOINT,
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