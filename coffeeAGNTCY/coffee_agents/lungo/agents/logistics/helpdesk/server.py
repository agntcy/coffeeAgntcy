import os
import asyncio
import logging
import uuid
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi import HTTPException, FastAPI, Request
from fastapi import FastAPI
from uvicorn import Config, Server
from starlette.routing import Route

from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.protocols.a2a.protocol import A2AProtocol
from ioa_observe.sdk.tracing import session_start

from agents.logistics.helpdesk.agent_executor import HelpdeskAgentExecutor
from agents.logistics.helpdesk.card import AGENT_CARD
from agents.logistics.helpdesk.graph import HelpdeskHistoryGraph  # assumes you saved earlier history graph
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT,
    TRANSPORT_SERVER_ENDPOINT,
    ENABLE_HTTP,
    FARM_BROADCAST_TOPIC,  # ensure this exists in config; if not, remove related usage
)

logger = logging.getLogger("lungo.helpdesk.server")
load_dotenv()

# Shared factory and graph
factory = AgntcyFactory("lungo_helpdesk", enable_tracing=True)
helpdesk_graph = HelpdeskHistoryGraph()

class PromptRequest(BaseModel):
    prompt: str

async def run_http_server(server: A2AStarletteApplication):
    app: FastAPI = server.build()

    async def liveness_probe(_request):
        try:
            transport = factory.create_transport(
                DEFAULT_MESSAGE_TRANSPORT,
                endpoint=TRANSPORT_SERVER_ENDPOINT,
                name="default/default/helpdesk_liveness",
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
            return JSONResponse({"error": "Timeout creating client"}, status_code=500)
        except Exception as e:
            return JSONResponse({"error": f"{e}"}, status_code=500)

    async def handle_prompt(request: Request):
        logger.info("Received /agent/prompt request")
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        try:
            body = PromptRequest(**data)
        except ValidationError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

        session_start()
        timeout_s = int(os.getenv("HELPDESK_TIMEOUT", "60"))
        try:
            result = await asyncio.wait_for(helpdesk_graph.serve(body.prompt), timeout=timeout_s)
            logger.info("Graph result: %s", result)
            return JSONResponse({"response": result})
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail=f"Request timed out after {timeout_s} seconds")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Unhandled error in handle_prompt")
            raise HTTPException(status_code=500, detail=f"Operation failed: {e}")

    # Attach liveness route
    app.router.routes.append(Route("/v1/health", liveness_probe, methods=["GET"]))
    app.router.routes.append(Route("/agent/prompt", handle_prompt, methods=["POST"]))

    try:
        config = Config(app=app, host="0.0.0.0", port=9094, loop="asyncio")
        server_uv = Server(config)
        await server_uv.serve()
    except Exception as e:
        logger.error("HTTP server error: %s", e)

async def run_transport(server: A2AStarletteApplication, transport_type: str, endpoint: str, block: bool):
    try:
        personal_topic = A2AProtocol.create_agent_topic(AGENT_CARD)
        transport = factory.create_transport(
            transport_type,
            endpoint=endpoint,
            name=f"default/default/{personal_topic}",
        )
        # Broadcast + private bridge (retain existing pattern)
        broadcast_bridge = factory.create_bridge(server, transport=transport, topic=FARM_BROADCAST_TOPIC)
        private_bridge = factory.create_bridge(server, transport=transport, topic=personal_topic)
        await broadcast_bridge.start(blocking=False)
        await private_bridge.start(blocking=block)
    except Exception as e:
        logger.error("Transport error: %s", e)

async def main(enable_http: bool):
    request_handler = DefaultRequestHandler(
        agent_executor=HelpdeskAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(agent_card=AGENT_CARD, http_handler=request_handler)

    tasks = []
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
        print("\nShutting down gracefully.")
    except Exception as e:
        print(f"Error occurred: {e}")