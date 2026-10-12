# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Grandma Helper API: the app talks to this; it talks to the agents over SLIM."""

import config.logging_config  # noqa: F401 - runs setup on import; must be first

import logging
import re
import secrets
from pathlib import Path

import uvicorn
from agntcy_app_sdk.factory import AgntcyFactory
from config.config import OTEL_SDK_DISABLED
from dotenv import load_dotenv
from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from ioa_observe.sdk.tracing import session_start
from opentelemetry import trace
from pydantic import BaseModel

from agents.supervisors.helper import pipeline

load_dotenv()
logger = logging.getLogger("helper.supervisor.main")

# Turns on tracing for the A2A calls, same as the Lungo supervisors.
AgntcyFactory("helper.supervisor", enable_tracing=not OTEL_SDK_DISABLED)
tracer = trace.get_tracer("helper.supervisor")

app = FastAPI(title="Grandma Helper")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Demo login: one built-in account, shown as a hint on the login screen.
# It only puts the demo behind a login screen; it is not real security.
DEMO_USERNAME = "grandma"
DEMO_PASSWORD = "demo123"
SESSION_COOKIE = "helper_demo_session"
# Logged-in sessions, in memory: restarting the server logs everyone out.
_sessions: set[str] = set()


class LoginRequest(BaseModel):
    username: str
    password: str


def require_login(
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> None:
    if session not in _sessions:
        raise HTTPException(status_code=401, detail="not logged in")


@app.post("/login")
async def login(req: LoginRequest, response: Response) -> dict:
    if req.username.strip().lower() != DEMO_USERNAME or req.password != DEMO_PASSWORD:
        raise HTTPException(status_code=401, detail="wrong username or password")
    token = secrets.token_urlsafe(16)
    _sessions.add(token)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax")
    return {"username": DEMO_USERNAME}


@app.post("/logout")
async def logout(
    response: Response,
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> dict:
    _sessions.discard(session)
    response.delete_cookie(SESSION_COOKIE)
    return {"status": "logged out"}


@app.get("/me", dependencies=[Depends(require_login)])
async def me() -> dict:
    return {"username": DEMO_USERNAME}


class TextRequest(BaseModel):
    text: str


def _require_text(req: TextRequest) -> str:
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text must not be empty")
    return text


async def _traced(kind: str, text: str, run) -> dict:
    """Run one request as a single trace (one session) so Grafana shows every
    agent call for this message together, with the final verdict on top."""
    with (
        session_start() as session,
        tracer.start_as_current_span(f"grandma_helper.{kind}") as span,
    ):
        span.set_attribute("helper.message", text)
        result = await run(text)
        span.set_attribute("helper.status", result["status"])
        span.set_attribute("helper.reasons", result["family"]["reasons"])
    result["session_id"] = session["executionID"]
    return result


@app.post("/explain", dependencies=[Depends(require_login)])
async def explain(req: TextRequest) -> dict:
    """An English message she received: translate, check for scams, advise."""
    return await _traced("explain", _require_text(req), pipeline.explain)


@app.post("/reply", dependencies=[Depends(require_login)])
async def reply(req: TextRequest) -> dict:
    """Her Mongolian reply, translated to English and double-checked."""
    return await _traced("reply", _require_text(req), pipeline.reply)


@app.get("/family/alerts", dependencies=[Depends(require_login)])
async def family_alerts() -> list[dict]:
    """Everything that was not plainly safe, newest first."""
    return pipeline.FAMILY_ALERTS


# Family contact emails, in memory like the sessions. Demo only: nothing is
# emailed to them yet.
_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
_family_contacts = {"primary": "", "secondary": ""}


class FamilyContacts(BaseModel):
    primary: str
    secondary: str = ""


@app.get("/family/contacts", dependencies=[Depends(require_login)])
async def get_family_contacts() -> dict:
    return _family_contacts


@app.put("/family/contacts", dependencies=[Depends(require_login)])
async def set_family_contacts(req: FamilyContacts) -> dict:
    primary, secondary = req.primary.strip(), req.secondary.strip()
    if not _EMAIL.fullmatch(primary):
        raise HTTPException(status_code=400, detail="family email is not valid")
    if secondary and not _EMAIL.fullmatch(secondary):
        raise HTTPException(status_code=400, detail="secondary email is not valid")
    _family_contacts.update(primary=primary, secondary=secondary)
    return _family_contacts


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    """The app itself: grandma's screen and the family screen."""
    return FileResponse(Path(__file__).with_name("static") / "index.html")


if __name__ == "__main__":
    uvicorn.run("agents.supervisors.helper.main:app", host="0.0.0.0", port=9200)
