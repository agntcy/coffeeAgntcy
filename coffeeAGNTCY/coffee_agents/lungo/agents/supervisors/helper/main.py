# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Grandma Helper API: the app talks to this; it talks to the agents over SLIM."""

import config.logging_config  # noqa: F401 - runs setup on import; must be first

import logging
from pathlib import Path

import uvicorn
from agntcy_app_sdk.factory import AgntcyFactory
from config.config import OTEL_SDK_DISABLED
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agents.supervisors.helper import pipeline

load_dotenv()
logger = logging.getLogger("helper.supervisor.main")

# Turns on tracing for the A2A calls, same as the Lungo supervisors.
AgntcyFactory("helper.supervisor", enable_tracing=not OTEL_SDK_DISABLED)

app = FastAPI(title="Grandma Helper")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TextRequest(BaseModel):
    text: str


def _require_text(req: TextRequest) -> str:
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text must not be empty")
    return text


@app.post("/explain")
async def explain(req: TextRequest) -> dict:
    """An English message she received: translate, check for scams, advise."""
    return await pipeline.explain(_require_text(req))


@app.post("/reply")
async def reply(req: TextRequest) -> dict:
    """Her Mongolian reply, translated to English and double-checked."""
    return await pipeline.reply(_require_text(req))


@app.get("/family/alerts")
async def family_alerts() -> list[dict]:
    """Everything that was not plainly safe, newest first."""
    return pipeline.FAMILY_ALERTS


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    """The app itself: grandma's screen and the family screen."""
    return FileResponse(Path(__file__).with_name("static") / "index.html")


if __name__ == "__main__":
    uvicorn.run("agents.supervisors.helper.main:app", host="0.0.0.0", port=9200)
