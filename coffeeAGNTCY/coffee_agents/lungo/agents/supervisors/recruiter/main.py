# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import config.logging_config  # noqa: F401 - runs setup on import; must be first

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Optional
from uuid import uuid4

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pathlib import Path
from pydantic import BaseModel
from agntcy_app_sdk.factory import AgntcyFactory

from common.cors import get_cors_allowed_origins

from agents.supervisors.recruiter import shared
from agents.supervisors.recruiter.card import RECRUITER_SUPERVISOR_CARD
from agents.supervisors.recruiter.recruiter_client import get_a2a_event_queue
from agents.supervisors.recruiter.recruiter_service_card import (
    RECRUITER_AGENT_URL,
)
from common.streaming_capability import require_streaming_capability
from config.config import LLM_MODEL, HOT_RELOAD_MODE, OTEL_SDK_DISABLED

logger = logging.getLogger("lungo.recruiter.supervisor.main")

load_dotenv()

# Initialize the shared agntcy factory (tracing from OTEL_SDK_DISABLED)
shared.set_factory(AgntcyFactory("lungo.recruiter_supervisor", enable_tracing=not OTEL_SDK_DISABLED))
require_streaming_capability("recruiter_supervisor", LLM_MODEL)

# Register the middleware cleanup SpanProcessor after the factory has
# initialized the OTel TracerProvider. This hook evicts per-trace state
# from a2a_event_middleware._in_flight when the caller's tool span ends.
if not OTEL_SDK_DISABLED:
    from common.a2a_event_middleware import register_cleanup_span_processor
    register_cleanup_span_processor()


def _load_agent_module():
    import agents.supervisors.recruiter.agent as agent_module  # noqa: F401
    return agent_module


@asynccontextmanager
async def lifespan(app: FastAPI):
    async def init_agent():
        try:
            agent_module = await asyncio.to_thread(_load_agent_module)
            app.state.agent_module = agent_module
            app.state.recruiter_ready = True
            logger.info("Recruiter agent initialized")
        except Exception as e:
            logger.exception("Background agent init failed: %s", e)

    init_task = asyncio.create_task(init_agent())
    try:
        yield
    finally:
        init_task.cancel()
        try:
            await init_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)
_cors_origins = get_cors_allowed_origins()
logger.info("CORS allow_origins: %s", _cors_origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None


@app.post("/agent/prompt")
async def handle_prompt(request: PromptRequest, req: Request):
    """Send prompt to the recruiter supervisor ADK agent and return the result."""
    if not getattr(req.app.state, "recruiter_ready", False):
        raise HTTPException(status_code=503, detail="Service initializing")
    agent_module = getattr(req.app.state, "agent_module", None)
    if agent_module is None:
        raise HTTPException(status_code=503, detail="Service initializing")
    try:
        session_id = request.session_id or "default_session"  # or str(uuid4())
        result = await agent_module.call_agent(
            query=request.prompt,
            session_id=session_id,
        )
        # Build response matching original API format
        response: dict = {
            "response": result["response"],
            "session_id": result["session_id"],
        }
        if result.get("agent_records"):
            response["agent_records"] = result["agent_records"]
        if result.get("evaluation_results"):
            response["evaluation_results"] = result["evaluation_results"]
        response["selected_agent"] = result.get("selected_agent")
        return response
    except Exception as e:
        logger.error(f"Error handling prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")


@app.post("/agent/prompt/stream")
async def handle_stream_prompt(request: PromptRequest, req: Request):
    """Stream recruiter supervisor agent responses as NDJSON lines."""
    if not getattr(req.app.state, "recruiter_ready", False):
        raise HTTPException(status_code=503, detail="Service initializing")
    agent_module = getattr(req.app.state, "agent_module", None)
    if agent_module is None:
        raise HTTPException(status_code=503, detail="Service initializing")
    try:
        session_id = request.session_id or "default_session"  # or str(uuid4())
        user_id = "default_user"

        async def stream_generator():
            try:
                final_sid = session_id
                a2a_queue = get_a2a_event_queue()

                # Drain any stale events from previous requests
                while not a2a_queue.empty():
                    try:
                        a2a_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                # Use an asyncio.Queue to merge ADK events and A2A side-channel events.
                # Both producers push dicts onto merged_queue; the consumer loop below
                # serialises them as NDJSON lines.
                merged_queue: asyncio.Queue[dict | None] = asyncio.Queue()

                async def _adk_producer():
                    """Iterate the ADK runner and push formatted events."""
                    nonlocal final_sid
                    try:
                        async for event, sid in agent_module.stream_agent(
                            query=request.prompt,
                            session_id=session_id,
                        ):
                            final_sid = sid

                            # Extract text content
                            msg_text = None
                            if event.content and event.content.parts:
                                for part in event.content.parts:
                                    if hasattr(part, "text") and part.text:
                                        msg_text = part.text
                                        break

                            # Extract function call / response info
                            function_calls = event.get_function_calls() if hasattr(event, "get_function_calls") else []
                            function_responses = event.get_function_responses() if hasattr(event, "get_function_responses") else []

                            # Fetch selected_agent on every event
                            current_selected_agent = await agent_module.get_selected_agent(user_id, final_sid)

                            if event.is_final_response():
                                agent_records = await agent_module.get_recruited_agents(user_id, final_sid)
                                evaluation_results = await agent_module.get_evaluation_results(user_id, final_sid)

                                line: dict = {
                                    "response": {
                                        "event_type": "completed",
                                        "message": msg_text,
                                        "state": "completed",
                                        "selected_agent": current_selected_agent,
                                    },
                                    "session_id": final_sid,
                                }
                                if agent_records:
                                    line["response"]["agent_records"] = agent_records
                                if evaluation_results:
                                    line["response"]["evaluation_results"] = evaluation_results
                                await merged_queue.put(line)
                            elif msg_text:
                                await merged_queue.put({
                                    "response": {
                                        "event_type": "status_update",
                                        "message": msg_text,
                                        "state": "working",
                                        "author": event.author,
                                        "selected_agent": current_selected_agent,
                                    },
                                    "session_id": sid,
                                })
                            elif function_calls and not event.partial:
                                for fc in function_calls:
                                    await merged_queue.put({
                                        "response": {
                                            "event_type": "status_update",
                                            "message": f"Calling tool: {fc.name}",
                                            "state": "working",
                                            "author": event.author,
                                            "selected_agent": current_selected_agent,
                                        },
                                        "session_id": sid,
                                    })
                            elif function_responses and not event.partial:
                                for fr in function_responses:
                                    await merged_queue.put({
                                        "response": {
                                            "event_type": "status_update",
                                            "message": f"Tool {fr.name} completed",
                                            "state": "working",
                                            "author": event.author,
                                            "selected_agent": current_selected_agent,
                                        },
                                        "session_id": sid,
                                    })
                    except Exception as e:
                        logger.error(f"Error in ADK stream: {e}", exc_info=True)
                        await merged_queue.put({
                            "response": {"event_type": "error", "message": str(e)}
                        })
                    finally:
                        # Signal that the ADK producer is done
                        await merged_queue.put(None)

                async def _a2a_side_channel_producer():
                    """Forward A2A streaming events from the recruiter_client queue."""
                    try:
                        while True:
                            # Wait for an A2A event from the tool's side-channel
                            a2a_event = await a2a_queue.get()
                            if a2a_event is None:
                                # Tool invocation finished; stop forwarding
                                break
                            await merged_queue.put({
                                "response": a2a_event,
                                "session_id": final_sid,
                            })
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.error(f"Error in A2A side-channel: {e}", exc_info=True)

                # Launch both producers concurrently
                adk_task = asyncio.create_task(_adk_producer())
                a2a_task = asyncio.create_task(_a2a_side_channel_producer())

                # Consume merged events and yield NDJSON lines
                try:
                    while True:
                        line = await merged_queue.get()
                        if line is None:
                            # ADK producer finished — we're done
                            break
                        yield json.dumps(line) + "\n"
                finally:
                    # Clean up: cancel the A2A side-channel if still running
                    if not a2a_task.done():
                        a2a_task.cancel()
                    # Ensure both tasks are awaited
                    await asyncio.gather(adk_task, a2a_task, return_exceptions=True)

            except Exception as e:
                logger.error(f"Error in stream: {e}", exc_info=True)
                yield json.dumps(
                    {"response": {"event_type": "error", "message": str(e)}}
                ) + "\n"

        return StreamingResponse(
            stream_generator(),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
    except Exception as e:
        logger.error(f"Error setting up stream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")


@app.get("/.well-known/agent-card.json")
async def agent_card():
    """Return the A2A AgentCard for this recruiter supervisor."""
    return RECRUITER_SUPERVISOR_CARD.model_dump(by_alias=True, exclude_none=True)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/v1/ready")
async def recruiter_init_ready(req: Request):
    """Process readiness: background agent init finished (no outbound I/O).

    Use this for cheap readiness probes (e.g. TestClient fixtures). Deep
    connectivity remains on ``/v1/health``.
    """
    if not getattr(req.app.state, "recruiter_ready", False):
        raise HTTPException(status_code=503, detail="Service initializing")
    return {"status": "ready"}


@app.get("/v1/health")
async def connectivity_health(req: Request):
    """Deep liveness: check that the recruiter A2A service is reachable."""
    if not getattr(req.app.state, "recruiter_ready", False):
        raise HTTPException(status_code=503, detail="Service initializing")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            resp = await client.get(f"{RECRUITER_AGENT_URL}/.well-known/agent.json")
            resp.raise_for_status()
        return {"status": "alive"}
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Recruiter service returned {e.response.status_code}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Cannot reach recruiter service: {str(e)}"
        )


@app.get("/transport/config")
async def get_config():
    return {"transport": "A2A_HTTP"}


@app.get("/suggested-prompts")
async def get_prompts(pattern: str = "default"):
    """Fetch suggested prompts for the recruiter supervisor."""
    try:
        prompts_path = Path(__file__).resolve().parent / "suggested_prompts.json"
        raw = prompts_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return {"recruiter": data.get("recruiter_prompts", [])}
    except Exception as e:
        logger.error(f"Unexpected error while reading prompts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while reading prompts.",
        )


@app.get("/agents/{slug}/oasf")
async def get_agent_oasf(slug: str):
    """Returns the OASF JSON for the specified agent slug from the static files."""
    oasf_path = Path(__file__).resolve().parent / "oasf" / "agents" / f"{slug}.json"
    if not oasf_path.exists():
        raise HTTPException(status_code=404, detail="OASF record not found")
    try:
        with oasf_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Failed to read OASF file for slug '{slug}': {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving the agent information. Please try again later.",
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8882, reload=HOT_RELOAD_MODE)
