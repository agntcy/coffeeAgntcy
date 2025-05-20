import asyncio
import argparse

from gateway_sdk.factory import TransportTypes
from gateway_sdk.factory import GatewayFactory

from a2a.server import A2AServer
from a2a.server.request_handlers import DefaultA2ARequestHandler

from agent_executor import FarmAgentExecutor
from config.config import AGP_GATEWAY_URL, DEFAULT_MESSAGE_TRANSPORT
from card import AGENT_CARD

async def main(transport_type: str, transport_endpoint: str | None):
    """Run the A2A server with the Farm Agent."""

    request_handler = DefaultA2ARequestHandler(
        agent_executor=FarmAgentExecutor()
    )

    server = A2AServer(agent_card=AGENT_CARD, request_handler=request_handler)

    # Gateway bridge to relay messages from the gateway message layer to the A2A server
    factory = GatewayFactory()
    transport = factory.create_transport(transport_type, transport_endpoint)
    bridge = factory.create_bridge(server, transport=transport)
    await bridge.start()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run the A2A farm server with a specified transport layer.")
    
    parser.add_argument(
        "--transport", 
        type=str, 
        choices=[t.value for t in TransportTypes], 
        default=DEFAULT_MESSAGE_TRANSPORT,
        help="Message layer type")
    
    parser.add_argument(
        "--endpoint", 
        type=str, 
        default=AGP_GATEWAY_URL, 
        help="Endpoint for the transport")

    args = parser.parse_args()

    try:
        asyncio.run(main(args.transport, args.endpoint))
    except KeyboardInterrupt:
        print("\nShutting down gracefully on keyboard interrupt.")
    except Exception as e:
        print(f"Error occurred: {e}")