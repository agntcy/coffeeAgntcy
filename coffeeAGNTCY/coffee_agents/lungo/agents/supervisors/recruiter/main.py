# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from typing import Optional
from uuid import uuid4

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pathlib import Path
from pydantic import BaseModel

from agents.supervisors.recruiter.agent import call_agent, stream_agent
from agents.supervisors.recruiter.card import RECRUITER_SUPERVISOR_CARD
from agents.supervisors.recruiter.recruiter_service_card import (
    RECRUITER_AGENT_URL,
)
from config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("lungo.recruiter.supervisor.main")

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None


@app.post("/agent/prompt")
async def handle_prompt(request: PromptRequest):
    """Send prompt to the recruiter supervisor ADK agent and return the result."""
    try:
        session_id = request.session_id or str(uuid4())
        response_text, session_id = await call_agent(
            query=request.prompt,
            session_id=session_id,
        )
        return {"response": response_text, "session_id": session_id}
    except Exception as e:
        logger.error(f"Error handling prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")


@app.post("/agent/prompt/stream")
async def handle_stream_prompt(request: PromptRequest):
    """Stream recruiter supervisor agent responses as NDJSON lines."""
    try:
        session_id = request.session_id or str(uuid4())

        async def stream_generator():
            try:
                async for event, sid in stream_agent(
                    query=request.prompt,
                    session_id=session_id,
                ):
                    # Build an NDJSON line from each ADK event
                    msg_text = None
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, "text") and part.text:
                                msg_text = part.text
                                break

                    if event.is_final_response():
                        line = {
                            "response": {
                                "event_type": "completed",
                                "message": msg_text,
                                "state": "completed",
                            },
                            "session_id": sid,
                        }
                        yield json.dumps(line) + "\n"
                    elif msg_text:
                        line = {
                            "response": {
                                "event_type": "status_update",
                                "message": msg_text,
                                "state": "working",
                                "author": event.author,
                            },
                            "session_id": sid,
                        }
                        yield json.dumps(line) + "\n"
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


@app.get("/v1/health")
async def connectivity_health():
    """Deep liveness: check that the recruiter A2A service is reachable."""
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
    uvicorn.run("main:app", host="0.0.0.0", port=8882, reload=True)
