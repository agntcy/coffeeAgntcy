# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import config.logging_config  # noqa: F401 - runs setup on import; must be first

import asyncio
import logging
from os import getenv

from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.types import AgentCard
from dotenv import load_dotenv
from uvicorn import Config, Server

from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware.cors import CORSMiddleware

from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.semantic.a2a.client.factory import A2AClientFactory
from agntcy_app_sdk.semantic.a2a import (
    ClientConfig,
    SlimTransportConfig,
)

from common.cors import get_cors_allowed_origins

from agents.logistics.farm.agent_executor import FarmAgentExecutor
from agents.logistics.farm.card import AGENT_CARD
from agents.logistics.shipper.card import AGENT_CARD as SHIPPER_AGENT_CARD
from config.config import (
    SLIM_SERVER,
    OTEL_SDK_DISABLED,
)

PORT = getenv("AGENT_PORT", "9093")

load_dotenv()

# Initialize a multi-protocol, multi-transport agntcy factory.
factory = AgntcyFactory("lungo.logistics_farm", enable_tracing=not OTEL_SDK_DISABLED)

logger = logging.getLogger("lungo.logistics.farm.server")


async def liveness_probe(request):
    """
    Uses the Shipper Agent to create a PointToPoint SLIM session (via A2A protocol)
    in order to verify connectivity with SLIM. If the session creation succeeds
    within the timeout, SLIM is considered 'alive'.
    """
    config = ClientConfig(
        slim_config=SlimTransportConfig(
            endpoint=f"http://{SLIM_SERVER}",
            name="lungo/agents/farm_agent",
            shared_secret_identity=getenv("SLIM_SHARED_SECRET", "slim-shared-secret-REPLACE_WITH_RANDOM_32PLUS_CHARS"),
        ),
    )

    # -- A2A client factory --
    a2a_client_factory = A2AClientFactory(config)

    try:
        # checks connectivity with the SLIM server and should succeed within the timeout if SLIM is alive
        await asyncio.wait_for(
            a2a_client_factory.create(SHIPPER_AGENT_CARD),
            timeout=30
        )
        logger.info("Liveness probe succeeded: SLIM connectivity verified.")
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
    cors_origins = get_cors_allowed_origins()
    logger.info("CORS allow_origins: %s", cors_origins)
    app_ = a2a_app.build()
    app_.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app_.router.routes.append(Route("/v1/health", liveness_probe, methods=["GET"]))
    return app_

def create_app() -> FastAPI:
    request_handler = DefaultRequestHandler(
        agent_executor=FarmAgentExecutor(),
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
        config = Config(app=app_, host="0.0.0.0", port=int(PORT), loop="asyncio")
        userver = Server(config)
        await userver.serve()
    except Exception as e:
        logger.error(f"HTTP server encountered an error: {e}")


async def serve_all_a2a_interfaces(
    request_handler: DefaultRequestHandler,
    agent_card: AgentCard,
):
    """Serve the Tatooine Farm agent across all A2A transports defined in its AgentCard.

    Creates an AgntcyFactory application session and registers every transport
    interface declared in the card's ``additional_interfaces``, which include:

    - **slim** – SLIM-based group communication transport
    - **slimrpc** – point-to-point transport for direct client-agent communication

    The card's ``preferred_transport`` (slim) determines the primary ``url``
    advertised to callers.  The session runs without keep-alive so it can be
    composed alongside the optional HTTP server via ``asyncio.gather``.

    Args:
        request_handler: The A2A request handler wired to the
            :class:`FarmAgentExecutor` and an in-memory task store.
        agent_card: The ``AgentCard`` describing this agent's capabilities,
            skills, and transport interfaces.
    """

    session = factory.create_app_session()
    await session.add_a2a_card(agent_card, request_handler).start(keep_alive=False)
    logger.info("Agent ready")

async def main():

    request_handler = DefaultRequestHandler(
        agent_executor=FarmAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=AGENT_CARD, http_handler=request_handler
    )

    # run the agent on all A2A interfaces defined in the card and always serve the HTTP health endpoint
    tasks = [asyncio.create_task(serve_all_a2a_interfaces(request_handler, AGENT_CARD))]
    tasks.append(asyncio.create_task(run_http_server(server)))

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully on keyboard interrupt.")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
