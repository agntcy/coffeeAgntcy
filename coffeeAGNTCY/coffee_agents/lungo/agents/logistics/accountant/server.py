# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging

from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from dotenv import load_dotenv
from uvicorn import Config, Server

from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware.cors import CORSMiddleware

from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.semantic.a2a.protocol import A2AProtocol
from agntcy_app_sdk.app_sessions import AppContainer

from agents.logistics.accountant.agent_executor import AccountantAgentExecutor
from agents.logistics.accountant.card import AGENT_CARD
from agents.logistics.shipper.card import AGENT_CARD as SHIPPER_AGENT_CARD
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT,
    TRANSPORT_SERVER_ENDPOINT,
    ENABLE_HTTP
)

load_dotenv()

# Initialize a multi-protocol, multi-transport agntcy factory.
factory = AgntcyFactory("lungo.logistics_accountant", enable_tracing=True)

logger = logging.getLogger("lungo.logistics.accountant.server")


async def liveness_probe(request):
    """
    Uses the Shipper Agent to create a PointToPoint SLIM session (via A2A protocol)
    in order to verify connectivity with SLIM. If the session creation succeeds
    within the timeout, SLIM is considered 'alive'.
    """
    try:
        transport = factory.create_transport(
            DEFAULT_MESSAGE_TRANSPORT,
            endpoint=TRANSPORT_SERVER_ENDPOINT,
            name="default/default/liveness_probe"
        )
        _ = await asyncio.wait_for(
            factory.create_client(
                "A2A",
                agent_topic=A2AProtocol.create_agent_topic(SHIPPER_AGENT_CARD),
                transport=transport
            ),
            timeout=30
        )
        return JSONResponse({"status": "alive"})
    except asyncio.TimeoutError:
        return JSONResponse(
            {
                "error": "Timeout occurred while creating client."
            },
            status_code=500
        )
    except Exception as e:
        return JSONResponse(
            {
                "error": f"Error occurred: {str(e)}"
            },
            status_code=500
        )

def build_http_server(a2a_app: A2AStarletteApplication) -> FastAPI:
    app_ = a2a_app.build()
    app_.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app_.router.routes.append(Route("/v1/health", liveness_probe, methods=["GET"]))
    return app_

def create_app() -> FastAPI:
    request_handler = DefaultRequestHandler(
        agent_executor=AccountantAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=AGENT_CARD, http_handler=request_handler
    )

    return build_http_server(server)

# Expose module-level app for pytest fixture
app = create_app()

async def run_http_server(server):
    # Add the liveness route to the FastAPI app
    app_ = server.build()
    app_.router.routes.append(Route("/v1/health", liveness_probe, methods=["GET"]))

    try:
        config = Config(app=app_, host="0.0.0.0", port=9092, loop="asyncio")
        userver = Server(config)
        await userver.serve()
    except Exception as e:
        logger.error(f"HTTP server encountered an error: {e}")

async def run_transport(server, transport_type, endpoint):
    """Run the transport and broadcast bridge."""
    try:
        personal_topic = A2AProtocol.create_agent_topic(AGENT_CARD)
        transport = factory.create_transport(transport_type, endpoint=endpoint, name=f"default/default/{personal_topic}")
        # Create an application session
        app_session = factory.create_app_session(max_sessions=1)

        # Add container for group communication
        app_session.add_app_container("group_session", AppContainer(
            server,
            transport=transport
        ))

        await app_session.start_session("group_session")

    except Exception as e:
        logger.error(f"Transport encountered an error: {e}")
        await app_session.stop_all_sessions()

async def main(enable_http: bool):
    """Run the A2A server with both HTTP and transport logic."""
    request_handler = DefaultRequestHandler(
        agent_executor=AccountantAgentExecutor(),
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
        logger.info("Shutting down gracefully on keyboard interrupt.")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
