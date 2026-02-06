# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from uuid import uuid4

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pathlib import Path
from pydantic import BaseModel

from a2a.client import ClientFactory, ClientConfig
from a2a.types import (
    DataPart,
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TaskStatusUpdateEvent,
    TextPart,
)

from agents.supervisors.recruiter.recruiter_service_card import (
    RECRUITER_AGENT_CARD,
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


def _extract_parts(parts: list[Part]) -> tuple[str | None, dict | None, dict | None]:
    """Extract text, found_agent_records, and evaluation_results from message parts."""
    text = None
    agent_records = None
    evaluation_results = None
    for part in parts:
        root = part.root
        if isinstance(root, TextPart):
            text = root.text
        elif isinstance(root, DataPart):
            meta_type = root.metadata.get("type") if root.metadata else None
            if meta_type == "found_agent_records":
                agent_records = root.data
            elif meta_type == "evaluation_results":
                evaluation_results = root.data
    return text, agent_records, evaluation_results


@app.post("/agent/prompt")
async def handle_prompt(request: PromptRequest):
    """Send prompt to the recruiter A2A agent (non-streaming) and return the result."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as httpx_client:
            config = ClientConfig(httpx_client=httpx_client, streaming=False)
            factory = ClientFactory(config)
            client = factory.create(RECRUITER_AGENT_CARD)

            print(f"Sending prompt to recruiter agent at {RECRUITER_AGENT_URL}: {request.prompt}")

            message = Message(
                role=Role.user,
                message_id=str(uuid4()),
                parts=[Part(root=TextPart(text=request.prompt))],
            )

            text_response = None
            agent_records = None
            evaluation_results = None
            session_id = str(uuid4())

            async for response in client.send_message(message):
                # Handle direct Message response
                if isinstance(response, Message):
                    text_response, agent_records, evaluation_results = _extract_parts(
                        response.parts
                    )

                # Handle (Task, update) tuple response
                elif isinstance(response, tuple) and len(response) == 2:
                    task, _update = response
                    if (
                        isinstance(task, Task)
                        and task.status.state == TaskState.completed
                        and task.status.message
                    ):
                        text_response, agent_records, evaluation_results = (
                            _extract_parts(task.status.message.parts)
                        )

            result: dict = {"response": text_response, "session_id": session_id}
            if agent_records is not None:
                result["agent_records"] = agent_records
            if evaluation_results is not None:
                result["evaluation_results"] = evaluation_results
            return result

    except Exception as e:
        logger.error(f"Error handling prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")


@app.post("/agent/prompt/stream")
async def handle_stream_prompt(request: PromptRequest):
    """Stream recruiter agent responses as NDJSON lines."""
    try:
        session_id = str(uuid4())

        async def stream_generator():
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(120.0)
                ) as httpx_client:
                    config = ClientConfig(httpx_client=httpx_client, streaming=True)
                    factory = ClientFactory(config)
                    client = factory.create(RECRUITER_AGENT_CARD)

                    message = Message(
                        role=Role.user,
                        message_id=str(uuid4()),
                        parts=[Part(root=TextPart(text=request.prompt))],
                    )

                    async for response in client.send_message(message):
                        # Handle (Task, TaskStatusUpdateEvent) tuples
                        if isinstance(response, tuple) and len(response) == 2:
                            task, update = response

                            if not isinstance(task, Task):
                                continue

                            if isinstance(update, TaskStatusUpdateEvent):
                                metadata = {}
                                msg_text = None

                                if update.status.message:
                                    metadata = update.status.message.metadata or {}
                                    # Extract text from message parts
                                    for part in update.status.message.parts:
                                        if isinstance(part.root, TextPart):
                                            msg_text = part.root.text
                                            break

                                event_type = metadata.get(
                                    "event_type", "status_update"
                                )
                                state = (
                                    update.status.state.value
                                    if update.status.state
                                    else "working"
                                )

                                # Final event — include full extracted data
                                if update.final and update.status.state == TaskState.completed:
                                    text, agent_records, evaluation_results = (
                                        _extract_parts(
                                            update.status.message.parts
                                        )
                                        if update.status.message
                                        else (None, None, None)
                                    )
                                    line = {
                                        "response": {
                                            "event_type": "completed",
                                            "message": text or msg_text,
                                            "state": state,
                                        },
                                        "session_id": session_id,
                                    }
                                    if agent_records is not None:
                                        line["response"]["agent_records"] = agent_records
                                    if evaluation_results is not None:
                                        line["response"]["evaluation_results"] = evaluation_results
                                    yield json.dumps(line) + "\n"
                                else:
                                    # Intermediate event
                                    line = {
                                        "response": {
                                            "event_type": event_type,
                                            "message": msg_text,
                                            "state": state,
                                        },
                                        "session_id": session_id,
                                    }
                                    # Forward extra metadata fields
                                    for key in ("tool_name", "to_agent", "from_agent"):
                                        if key in metadata:
                                            line["response"][key] = metadata[key]
                                    yield json.dumps(line) + "\n"

            except Exception as e:
                logger.error(f"Error in stream: {e}", exc_info=True)
                yield json.dumps({"response": {"event_type": "error", "message": str(e)}}) + "\n"

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
