# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
from datetime import datetime, timezone
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.routing import Route
from uvicorn import Config, Server
from starlette.middleware.cors import CORSMiddleware

from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.protocols.a2a.protocol import A2AProtocol
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from agents.logistics.helpdesk.agent_executor import HelpdeskAgentExecutor
from agents.logistics.helpdesk.card import AGENT_CARD
from agents.logistics.helpdesk.stream import stream_handler
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT,
    ENABLE_HTTP,
    FARM_BROADCAST_TOPIC,
    TRANSPORT_SERVER_ENDPOINT,
)

from agents.logistics.helpdesk.store.singleton import global_store

logger = logging.getLogger("lungo.helpdesk.server")
load_dotenv()

factory = AgntcyFactory("lungo_helpdesk", enable_tracing=True)

class PromptRequest(BaseModel):
    prompt: str


def utc_timestamp() -> str:
    """Return current UTC timestamp in ISO 8601 (milliseconds)."""
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(timespec="milliseconds")


async def health_handler(_request: Request) -> JSONResponse:
    """Liveness probe ensuring transport + client creation succeeds within timeout."""
    try:
        transport = factory.create_transport(
            DEFAULT_MESSAGE_TRANSPORT,
            endpoint=TRANSPORT_SERVER_ENDPOINT,
            name="default/default/helpdesk_liveness",
        )
        await asyncio.wait_for(
            factory.create_client(
                "A2A",
                agent_topic=A2AProtocol.create_agent_topic(AGENT_CARD),
                transport=transport,
            ),
            timeout=30,
        )
        return JSONResponse({"status": "alive"})
    except asyncio.TimeoutError:
        return JSONResponse({"error": "Timeout creating client"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)



def build_http_app(a2a_app: A2AStarletteApplication) -> FastAPI:
    """Attach REST endpoints to the underlying Starlette application."""
    app = a2a_app.build()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Replace "*" with specific origins if needed
        allow_credentials=True,
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
    )
    app.router.routes.append(Route("/v1/health", health_handler, methods=["GET"]))
    app.router.routes.append(Route("/agent/chat-logs", stream_handler, methods=["GET"]))
    return app


async def run_http_server(server: A2AStarletteApplication):
    """Run the FastAPI/Starlette HTTP server."""
    app = build_http_app(server)
    try:
        config = Config(app=app, host="0.0.0.0", port=9094, loop="asyncio")
        uvicorn_server = Server(config)
        await uvicorn_server.serve()
    except Exception as e:
        logger.error("HTTP server error: %s", e)


async def run_transport(
        server: A2AStarletteApplication,
        transport_type: str,
        endpoint: str,
        block: bool,
):
    """Initialize and run transport bridges (broadcast + private)."""
    try:
        personal_topic = A2AProtocol.create_agent_topic(AGENT_CARD)
        transport = factory.create_transport(
            transport_type,
            endpoint=endpoint,
            name=f"default/default/{personal_topic}",
        )
        broadcast_bridge = factory.create_bridge(server, transport=transport, topic=FARM_BROADCAST_TOPIC)
        private_bridge = factory.create_bridge(server, transport=transport, topic=personal_topic)
        await broadcast_bridge.start(blocking=False)
        await private_bridge.start(blocking=block)
    except Exception as e:
        logger.error("Transport error: %s", e)


async def main(enable_http: bool):
    """Entry point orchestrating HTTP server and transport runtime."""
    request_handler = DefaultRequestHandler(
        agent_executor=HelpdeskAgentExecutor(store=global_store),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(agent_card=AGENT_CARD, http_handler=request_handler)

    tasks: List[asyncio.Task] = []
    if enable_http:
        tasks.append(asyncio.create_task(run_http_server(server)))
    tasks.append(
        asyncio.create_task(
            run_transport(
                server,
                DEFAULT_MESSAGE_TRANSPORT,
                TRANSPORT_SERVER_ENDPOINT,
                block=True,
            )
        )
    )
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main(ENABLE_HTTP))
    except KeyboardInterrupt:
        print("Shutting down gracefully.")
    except Exception as e:
        print(f"Error occurred: {e}")
