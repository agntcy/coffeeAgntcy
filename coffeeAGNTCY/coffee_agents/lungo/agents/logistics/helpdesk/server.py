import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from sse_starlette.sse import EventSourceResponse
from starlette.routing import Route
from uvicorn import Config, Server

from agntcy_app_sdk.factory import AgntcyFactory
from agntcy_app_sdk.protocols.a2a.protocol import A2AProtocol
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from agents.logistics.helpdesk.agent_executor import HelpdeskAgentExecutor
from agents.logistics.helpdesk.card import AGENT_CARD
from agents.logistics.helpdesk.graph import HelpdeskHistoryGraph
from common.logistic_states import LogisticStatus
from config.config import (
    DEFAULT_MESSAGE_TRANSPORT,
    ENABLE_HTTP,
    FARM_BROADCAST_TOPIC,
    TRANSPORT_SERVER_ENDPOINT,
)
from ioa_observe.sdk.tracing import session_start

STREAM_DELAY_SECONDS = 0.75

logger = logging.getLogger("lungo.helpdesk.server")
load_dotenv()

factory = AgntcyFactory("lungo_helpdesk", enable_tracing=True)
helpdesk_graph = HelpdeskHistoryGraph()


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


async def prompt_handler(request: Request) -> JSONResponse:
    """Handle synchronous prompt requests served via the helpdesk history graph."""
    logger.info("Received /agent/prompt request")
    try:
        data = await request.json()
        body = PromptRequest(**data)
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

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
        logger.exception("Unhandled error in prompt_handler")
        raise HTTPException(status_code=500, detail=f"Operation failed: {e}")


async def fake_stream_sequence(prompt: str) -> List[Dict[str, str]]:
    """
    Deterministic fake logistics flow.
    Each step: sender, receiver, message, state.
    """
    flow = [
        ("Supervisor", "Tatooine Farm", LogisticStatus.RECEIVED_ORDER.value, "Received order"),
        ("Tatooine Farm", "Shipper", LogisticStatus.HANDOVER_TO_SHIPPER.value, "Handover to shipper"),
        ("Shipper", "Accountant", LogisticStatus.CUSTOMS_CLEARANCE.value, "Customs clearance"),
        ("Accountant", "Shipper", LogisticStatus.PAYMENT_COMPLETE.value, "Payment complete"),
        ("Shipper", "Supervisor", LogisticStatus.DELIVERED.value, "Delivered"),
    ]
    return [
        {
            "sender": send,
            "receiver": recv,
            "message": msg,
            "state": state,
        }
        for send, recv, state, msg in flow
    ]


async def sse_generator(request: Request, prompt: str) -> AsyncGenerator[dict, None]:
    """
    Stream the fake logistics sequence via Server-Sent Events.
    Marks the final record with `final=True`.
    """
    connection_id = str(uuid.uuid4())
    steps = await fake_stream_sequence(prompt)
    if not steps:
        return
    total = len(steps)

    for idx, step in enumerate(steps, start=1):
        if await request.is_disconnected():
            logger.info("SSE client disconnected")
            break
        is_final = idx == total
        payload = {
            "connection_id": connection_id,
            "sender": step["sender"],
            "receiver": step["receiver"],
            "message": step["message"],
            "timestamp": utc_timestamp(),
            "state": step["state"],
            "final": is_final,
        }
        yield {"data": json.dumps(payload)}
        if not is_final:
            await asyncio.sleep(STREAM_DELAY_SECONDS)


async def stream_handler(request: Request) -> EventSourceResponse:
    """HTTP endpoint for streaming the fake logistics flow."""
    prompt = request.query_params.get("prompt", "no prompt supplied")
    return EventSourceResponse(sse_generator(request, prompt))


def build_http_app(a2a_app: A2AStarletteApplication) -> FastAPI:
    """Attach REST endpoints to the underlying Starlette application."""
    app = a2a_app.build()
    app.router.routes.append(Route("/v1/health", health_handler, methods=["GET"]))
    app.router.routes.append(Route("/agent/prompt", prompt_handler, methods=["POST"]))
    app.router.routes.append(Route("/agent/stream", stream_handler, methods=["GET"]))
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
        agent_executor=HelpdeskAgentExecutor(),
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