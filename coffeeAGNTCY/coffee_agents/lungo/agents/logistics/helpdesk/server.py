# file: server.py
import os
import json
import asyncio
import logging
import uuid
from typing import AsyncGenerator, List, Dict
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.routing import Route
from uvicorn import Config, Server

STREAM_DELAY_SECONDS = 0.75

try:
    # Requires: pip install sse-starlette
    from sse_starlette.sse import EventSourceResponse
except ImportError as e:
    raise RuntimeError("Missing dependency 'sse-starlette'. Install with: pip install sse-starlette") from e

from pydantic import BaseModel, ValidationError

from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.request_handlers import DefaultRequestHandler
from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.protocols.a2a.protocol import A2AProtocol
from ioa_observe.sdk.tracing import session_start

from agents.logistics.helpdesk.agent_executor import HelpdeskAgentExecutor
from agents.logistics.helpdesk.card import AGENT_CARD
from agents.logistics.helpdesk.graph import HelpdeskHistoryGraph
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT,
    TRANSPORT_SERVER_ENDPOINT,
    ENABLE_HTTP,
    FARM_BROADCAST_TOPIC,
)

logger = logging.getLogger("lungo.helpdesk.server")
load_dotenv()

factory = AgntcyFactory("lungo_helpdesk", enable_tracing=True)
helpdesk_graph = HelpdeskHistoryGraph()


class PromptRequest(BaseModel):
    prompt: str


async def health_handler(_request: Request) -> JSONResponse:
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


async def prompt_handler(request: Request) -> JSONResponse:
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
        result = await asyncio.wait_for(
            helpdesk_graph.serve(body.prompt),
            timeout=timeout_s,
        )
        logger.info("Graph result: %s", result)
        return JSONResponse({"response": result})
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Request timed out after {timeout_s} seconds",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error in prompt_handler")
        raise HTTPException(status_code=500, detail=f"Operation failed: {e}")


async def fake_stream_sequence(prompt: str) -> List[Dict[str, str]]:
    # Construct a deterministic fake streaming sequence
    base = [
        "Acknowledged request",
        f"Processing prompt: {prompt[:50]}",
        "Retrieving related knowledge",
        "Synthesizing answer",
        "Finalizing response",
        "Done",
    ]
    return base




def utc_timestamp() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(timespec="milliseconds")

async def sse_generator(request: Request, prompt: str) -> AsyncGenerator[dict, None]:
    connection_id = str(uuid.uuid4())
    steps = await fake_stream_sequence(prompt)  # returns list[str]
    disconnected = False

    for idx, message in enumerate(steps, start=1):
        if await request.is_disconnected():
            logger.info("SSE client disconnected")
            disconnected = True
            break

        payload = {
            "connection_id": connection_id,
            "sender": "helpdesk",
            "receiver": "client",
            "message": message,
            "timestamp": utc_timestamp(),
            "final": False,
        }
        yield {
            "data": json.dumps(payload),
        }
        await asyncio.sleep(STREAM_DELAY_SECONDS)

    # Emit explicit final frame only if not disconnected
    if not disconnected:
        final_payload = {
            "connection_id": connection_id,
            "sender": "helpdesk",
            "receiver": "client",
            "message": "stream complete",
            "timestamp": utc_timestamp(),
            "final": True,
        }
        yield {
            "data": json.dumps(final_payload),
        }


async def stream_handler(request: Request) -> EventSourceResponse:
    # Optional prompt from query
    prompt = request.query_params.get("prompt", "no prompt supplied")
    return EventSourceResponse(sse_generator(request, prompt))


def build_http_app(a2a_app: A2AStarletteApplication) -> FastAPI:
    app = a2a_app.build()
    # Register routes
    app.router.routes.append(Route("/v1/health", health_handler, methods=["GET"]))
    app.router.routes.append(Route("/agent/prompt", prompt_handler, methods=["POST"]))
    app.router.routes.append(Route("/agent/stream", stream_handler, methods=["GET"]))
    return app


async def run_http_server(server: A2AStarletteApplication):
    app = build_http_app(server)
    try:
        config = Config(app=app, host="0.0.0.0", port=9094, loop="asyncio")
        server_uv = Server(config)
        await server_uv.serve()
    except Exception as e:
        logger.error("HTTP server error: %s", e)


async def run_transport(
        server: A2AStarletteApplication,
        transport_type: str,
        endpoint: str,
        block: bool,
):
    try:
        personal_topic = A2AProtocol.create_agent_topic(AGENT_CARD)
        transport = factory.create_transport(
            transport_type,
            endpoint=endpoint,
            name=f"default/default/{personal_topic}",
        )
        broadcast_bridge = factory.create_bridge(
            server, transport=transport, topic=FARM_BROADCAST_TOPIC
        )
        private_bridge = factory.create_bridge(
            server, transport=transport, topic=personal_topic
        )
        await broadcast_bridge.start(blocking=False)
        await private_bridge.start(blocking=block)
    except Exception as e:
        logger.error("Transport error: %s", e)


async def main(enable_http: bool):
    request_handler = DefaultRequestHandler(
        agent_executor=HelpdeskAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(
        agent_card=AGENT_CARD,
        http_handler=request_handler,
    )
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
        print("Shutting down gracefully.")
    except Exception as e:
        print(f"Error occurred: {e}")