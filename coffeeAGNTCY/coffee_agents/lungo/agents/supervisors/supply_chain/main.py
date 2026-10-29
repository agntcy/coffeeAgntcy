# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import logging
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path

import config.logging_config  # noqa: F401 - runs setup on import; must be first
import uvicorn
from agents.supervisors.supply_chain.card import BUYER_CARD
from agents.supervisors.supply_chain.runner import SupplyChainRunner
from agents.supervisors.supply_chain.selection import (
    L9_CONFIGURATIONS,
    L9_DISABLED_MESSAGE,
    validate_fields,
)
from agents.supervisors.supply_chain.shared import a2a_client_factory, set_factory
from agents.supervisors.supply_chain.transport import SlimGroupTransport
from agents.supply_chain.logistics.card import AGENT_CARD as LOGISTICS_CARD
from agents.supply_chain.supplier.card import AGENT_CARDS as SUPPLIER_CARDS
from agntcy_app_sdk.factory import AgntcyFactory
from common.a2a_event_middleware import EventEmittingInterceptor
from common.cors import get_cors_allowed_origins
from config.config import HOT_RELOAD_MODE, LLM_MODEL, OTEL_SDK_DISABLED
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from ioa_observe.sdk.tracing import session_start
from pydantic import BaseModel

logger = logging.getLogger("lungo.supply_chain.supervisor.main")

load_dotenv()

set_factory(
    AgntcyFactory("lungo.supply_chain_buyer", enable_tracing=not OTEL_SDK_DISABLED)
)

if not OTEL_SDK_DISABLED:
    from common.a2a_event_middleware.inflight import register_cleanup_span_processor

    register_cleanup_span_processor()


def _build_runner() -> SupplyChainRunner:
    cards = {"logistics": LOGISTICS_CARD, **SUPPLIER_CARDS}
    transport = SlimGroupTransport(
        a2a_client_factory,
        cards,
        interceptors=[EventEmittingInterceptor(caller_card=BUYER_CARD)],
    )
    return SupplyChainRunner(transport, model=LLM_MODEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async def init_runner():
        try:
            app.state.supply_chain_runner = await asyncio.to_thread(_build_runner)
            logger.info("Supply chain runner initialized")
        except Exception as e:
            logger.exception("Background runner init failed: %s", e)

    init_task = asyncio.create_task(init_runner())
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
    workflow_instance_id: str | None = None
    # Optional explicit selection. These take precedence over the prompt.
    case: str | None = None
    configuration: str | None = None


# Rejects malformed input early. Traversal is actually prevented by the
# containment check in get_agent_oasf below, not by this character set.
_SLUG_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _runner(req: Request) -> SupplyChainRunner:
    runner = getattr(req.app.state, "supply_chain_runner", None)
    if runner is None:
        raise HTTPException(status_code=503, detail="Service initializing")
    return runner


def _validated(request: PromptRequest, runner: SupplyChainRunner) -> None:
    try:
        validate_fields(request.case, request.configuration)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    if not runner.l9_enabled and request.configuration in L9_CONFIGURATIONS:
        raise HTTPException(status_code=400, detail=L9_DISABLED_MESSAGE)


@app.post("/agent/prompt")
async def handle_prompt(request: PromptRequest, req: Request):
    """Run to the end and return the selection, record and verdict."""
    runner = _runner(req)
    _validated(request, runner)
    try:
        with session_start() as session_id:
            result = await runner.run(
                request.prompt,
                case=request.case,
                configuration=request.configuration,
                workflow_instance_id=request.workflow_instance_id,
            )
            return {"response": result, "session_id": session_id["executionID"]}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Operation failed")
        raise HTTPException(status_code=500, detail=f"Operation failed: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/v1/health")
async def connectivity_health(req: Request):
    """Deep liveness: creating a client for the Logistics agent opens a SLIM session."""
    _runner(req)
    try:
        await asyncio.wait_for(a2a_client_factory.create(LOGISTICS_CARD), timeout=30)
        logger.info("Liveness probe succeeded: SLIM connectivity verified.")
        return {"status": "alive"}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=500, detail="Timeout creating A2A client")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/transport/config")
async def get_config():
    # The negotiation group runs over SLIM group sessions only.
    return {"transport": "SLIM"}


@app.post("/agent/prompt/stream")
async def handle_stream_prompt(request: PromptRequest, req: Request):
    """
    Streams a run as NDJSON. Every line is
    ``{"response": {"type": "status|message|record|verdict", ...}, "session_id": "..."}``.
    The first event states which case and configuration were chosen. The
    record and the verdict come last, after the run's ``RUN_END`` message.
    """
    runner = _runner(req)
    _validated(request, runner)
    with session_start() as session_id:

        async def stream_generator():
            try:
                async for event in runner.stream(
                    request.prompt,
                    case=request.case,
                    configuration=request.configuration,
                    workflow_instance_id=request.workflow_instance_id,
                ):
                    yield (
                        json.dumps(
                            {"response": event, "session_id": session_id["executionID"]}
                        )
                        + "\n"
                    )
            except Exception as e:
                logger.exception("Error in stream: %s", e)
                yield (
                    json.dumps(
                        {
                            "response": {
                                "type": "status",
                                "state": "error",
                                "message": "An internal error occurred while processing the request.",
                            }
                        }
                    )
                    + "\n"
                )

        return StreamingResponse(
            stream_generator(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )


@app.get("/suggested-prompts")
async def get_prompts(req: Request, pattern: str = "default"):
    """The suggested prompts, grouped by goal. With L9 off, only baseline ones."""
    try:
        prompts_path = Path(__file__).resolve().parent / "suggested_prompts.json"
        data = json.loads(prompts_path.read_text(encoding="utf-8"))
        prompts = data.get("supply_chain_prompts", [])
        # Until the runner exists, offer the safe list: no L9 prompt.
        runner = getattr(req.app.state, "supply_chain_runner", None)
        if runner is None or not runner.l9_enabled:
            prompts = [
                p for p in prompts if p["configuration"] not in L9_CONFIGURATIONS
            ]
        return {"supply_chain": prompts}
    except Exception as e:
        logger.error(f"Unexpected error while reading prompts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while reading prompts.",
        )


@app.get("/agents/{slug}/oasf")
async def get_agent_oasf(slug: str):
    """Returns the OASF JSON for the specified agent slug from the static files."""
    if not _SLUG_RE.fullmatch(slug):
        raise HTTPException(status_code=404, detail="OASF record not found")
    oasf_dir = os.path.realpath(
        os.path.join(os.path.dirname(__file__), "oasf", "agents")
    )
    oasf_path = os.path.realpath(os.path.join(oasf_dir, f"{slug}.json"))
    if not oasf_path.startswith(oasf_dir + os.sep) or not os.path.exists(oasf_path):
        raise HTTPException(status_code=404, detail="OASF record not found")
    try:
        with open(oasf_path, "r", encoding="utf-8") as f:
            return JSONResponse(content=json.load(f))
    except Exception as e:
        logger.error(f"Failed to read OASF file for slug '{slug}': {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving the agent information. Please try again later.",
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9095, reload=HOT_RELOAD_MODE)
