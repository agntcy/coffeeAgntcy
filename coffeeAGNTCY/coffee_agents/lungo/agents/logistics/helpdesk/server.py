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
from agntcy_app_sdk.semantic.a2a.protocol import A2AProtocol
from agntcy_app_sdk.app_sessions import AppContainer
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from agents.logistics.helpdesk.agent_executor import HelpdeskAgentExecutor
from agents.logistics.helpdesk.card import AGENT_CARD
from agents.logistics.shipper.card import AGENT_CARD as SHIPPER_AGENT_CARD
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT,
    ENABLE_HTTP,
    FARM_BROADCAST_TOPIC,
    TRANSPORT_SERVER_ENDPOINT,
)
from agents.logistics.helpdesk.store.singleton import global_store

logger = logging.getLogger("lungo.logistics.helpdesk.server")
load_dotenv()

factory = AgntcyFactory("lungo.logistics_helpdesk", enable_tracing=True)

class PromptRequest(BaseModel):
    prompt: str

def utc_timestamp() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(timespec="milliseconds")

async def health_handler(_request: Request) -> JSONResponse:
    """
    Uses the Shipper Agent to create a PointToPoint SLIM session (via A2A protocol)
    in order to verify connectivity with SLIM. If the session creation succeeds
    within the timeout, SLIM is considered 'alive'.
    """
    try:
        transport = factory.create_transport(
            DEFAULT_MESSAGE_TRANSPORT,
            endpoint=TRANSPORT_SERVER_ENDPOINT,
            name="default/default/helpdesk_liveness",
        )
        await asyncio.wait_for(
            factory.create_client(
                "A2A",
                agent_topic=A2AProtocol.create_agent_topic(SHIPPER_AGENT_CARD),
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
    app = a2a_app.build()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.router.routes.append(Route("/v1/health", health_handler, methods=["GET"]))
    return app

# New: factory + global FastAPI instance for tests/imports
def create_app() -> FastAPI:
    request_handler = DefaultRequestHandler(
        agent_executor=HelpdeskAgentExecutor(store=global_store),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(agent_card=AGENT_CARD, http_handler=request_handler)
    return build_http_app(server)

# Expose module-level app for pytest fixture
app = create_app()

async def run_http_server(server: A2AStarletteApplication):
    _app = build_http_app(server)
    try:
        config = Config(app=_app, host="0.0.0.0", port=9094, loop="asyncio")
        uvicorn_server = Server(config)
        await uvicorn_server.serve()
    except Exception as e:
        logger.error("HTTP server error: %s", e)

async def run_transport(server: A2AStarletteApplication, transport_type: str, endpoint: str):
    try:
        personal_topic = A2AProtocol.create_agent_topic(AGENT_CARD)
        transport = factory.create_transport(
            transport_type,
            endpoint=endpoint,
            name=f"default/default/{personal_topic}",
        )
        # Create an application session
        app_session = factory.create_app_session(max_sessions=1)

        # Add container for group communication
        app_session.add_app_container("group_session", AppContainer(
            server,
            transport=transport
        ))

        await app_session.start_session("group_session")
    except Exception as e:
        logger.error("Transport error: %s", e)
        await app_session.stop_all_sessions()

async def main(enable_http: bool):
    request_handler = DefaultRequestHandler(
        agent_executor=HelpdeskAgentExecutor(store=global_store),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(agent_card=AGENT_CARD, http_handler=request_handler)
    tasks: List[asyncio.Task] = []
    if enable_http:
        tasks.append(asyncio.create_task(run_http_server(server)))
    tasks.append(asyncio.create_task(run_transport(
        server,
        DEFAULT_MESSAGE_TRANSPORT,
        TRANSPORT_SERVER_ENDPOINT,
    )))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main(ENABLE_HTTP))
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully.")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
