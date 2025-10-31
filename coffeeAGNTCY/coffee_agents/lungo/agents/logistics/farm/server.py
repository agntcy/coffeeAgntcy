# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio

from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from dotenv import load_dotenv
from uvicorn import Config, Server

from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.protocols.a2a.protocol import A2AProtocol

from agents.logistics.farm.agent_executor import FarmAgentExecutor
from agents.logistics.farm.card import AGENT_CARD
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT,
    TRANSPORT_SERVER_ENDPOINT,
    ENABLE_HTTP
)

load_dotenv()

# Initialize a multi-protocol, multi-transport agntcy factory.
factory = AgntcyFactory("lungo.logistics_farm", enable_tracing=True)

async def run_http_server(server):
    """Run the HTTP/REST server."""
    from fastapi import FastAPI
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    # Define the liveness probe endpoint
    async def liveness_probe(request):
        try:
            transport = factory.create_transport(
                DEFAULT_MESSAGE_TRANSPORT,
                endpoint=TRANSPORT_SERVER_ENDPOINT,
                name="default/default/liveness_probe",
            )
            _ = await asyncio.wait_for(
                factory.create_client(
                    "A2A",
                    agent_topic=A2AProtocol.create_agent_topic(AGENT_CARD),
                    transport=transport,
                ),
                timeout=30,
            )
            return JSONResponse({"status": "alive"})
        except asyncio.TimeoutError:
            return JSONResponse({"error": "Timeout occurred while creating client."}, status_code=500)
        except Exception as e:
            return JSONResponse({"error": f"Error occurred: {str(e)}"}, status_code=500)

    # Add the liveness route to the FastAPI app
    app = server.build()
    app.router.routes.append(Route("/v1/health", liveness_probe, methods=["GET"]))

    try:
        config = Config(app=app, host="0.0.0.0", port=9093, loop="asyncio")
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
            server, transport=transport
        )
        
        await broadcast_bridge.start(blocking=False)

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

    # Run HTTP server and transport logic concurrently
    tasks = []
    if enable_http:
        tasks.append(asyncio.create_task(run_http_server(server)))
    tasks.append(asyncio.create_task(run_transport(server, DEFAULT_MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT, block=True)))

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    try:
        asyncio.run(main(ENABLE_HTTP))
    except KeyboardInterrupt:
        print("\nShutting down gracefully on keyboard interrupt.")
    except Exception as e:
        print(f"Error occurred: {e}")