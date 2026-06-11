# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Pattern chat: docs-grounded LLM advisor for POST /patterns/{name}/chat.

Per-pattern ADK Agent (instruction carries the pattern markdown) + a shared
InMemorySessionService keyed by (pattern, fe_session_id). Non-streaming
internally; the router wraps the response as one NDJSON chunk for now.
"""

from __future__ import annotations

import logging
import os
from threading import Lock

import litellm
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from api.agentic_workflows.workflow_documentation import (
    load_parsed_workflow_documentation,
    workflow_name_to_documentation_slug,
)
from config.config import LLM_MODEL


logger = logging.getLogger(__name__)

APP_NAME = "pattern_chat"
DEFAULT_USER_ID = "pattern-chat-user"


_LITELLM_PROXY_BASE_URL = os.getenv("LITELLM_PROXY_BASE_URL")
_LITELLM_PROXY_API_KEY = os.getenv("LITELLM_PROXY_API_KEY")
if _LITELLM_PROXY_API_KEY and _LITELLM_PROXY_BASE_URL:
    os.environ["LITELLM_PROXY_API_KEY"] = _LITELLM_PROXY_API_KEY
    os.environ["LITELLM_PROXY_API_BASE"] = _LITELLM_PROXY_BASE_URL
    litellm.use_litellm_proxy = True


BASE_SYSTEM_PROMPT = (
    "You are the AGNTCY patterns advisor. Ground your answers in the reference "
    "material below. Be helpful about implementation, trade-offs, and how the "
    "pattern composes; decline questions unrelated to agentic patterns."
)


def _instruction_for_pattern(pattern_name: str, full_markdown: str) -> str:
    return (
        f"{BASE_SYSTEM_PROMPT}\n\n"
        f"## Pattern in scope\n\n{pattern_name}\n\n"
        f"## Reference material\n\n{full_markdown}\n"
    )


_session_service = InMemorySessionService()
_runners: dict[str, Runner] = {}
_runners_lock = Lock()


class PatternReferenceNotFound(Exception):
    """No reference markdown exists for the requested pattern name."""

    def __init__(self, pattern_name: str):
        self.pattern_name = pattern_name
        super().__init__(f"No reference material for pattern: {pattern_name}")


def _get_or_build_runner(pattern_name: str) -> Runner:
    with _runners_lock:
        runner = _runners.get(pattern_name)
        if runner is not None:
            return runner

        slug = workflow_name_to_documentation_slug(pattern_name)
        parsed = load_parsed_workflow_documentation(slug)
        if parsed is None:
            raise PatternReferenceNotFound(pattern_name)

        agent = Agent(
            name=f"pattern_chat_{slug}",
            model=LiteLlm(model=LLM_MODEL),
            description=f"Docs-grounded advisor for the {pattern_name} agentic pattern.",
            instruction=_instruction_for_pattern(pattern_name, parsed.full_markdown),
            tools=[],
        )
        runner = Runner(agent=agent, app_name=APP_NAME, session_service=_session_service)
        _runners[pattern_name] = runner
        return runner


def _session_key(pattern_name: str, fe_session_id: str) -> str:
    return f"{pattern_name}::{fe_session_id}"


async def _ensure_session(pattern_name: str, fe_session_id: str) -> None:
    sid = _session_key(pattern_name, fe_session_id)
    existing = await _session_service.get_session(
        app_name=APP_NAME, user_id=DEFAULT_USER_ID, session_id=sid
    )
    if existing is None:
        await _session_service.create_session(
            app_name=APP_NAME, user_id=DEFAULT_USER_ID, session_id=sid
        )


async def run_one_turn(pattern_name: str, fe_session_id: str, user_message: str) -> str:
    """Run one user turn; raises PatternReferenceNotFound if the pattern has no doc."""
    runner = _get_or_build_runner(pattern_name)
    await _ensure_session(pattern_name, fe_session_id)

    sid = _session_key(pattern_name, fe_session_id)
    content = types.Content(role="user", parts=[types.Part(text=user_message)])

    final_response = ""
    async for event in runner.run_async(
        user_id=DEFAULT_USER_ID,
        session_id=sid,
        new_message=content,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text or ""
            break

    return final_response
