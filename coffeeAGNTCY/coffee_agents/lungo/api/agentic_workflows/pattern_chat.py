# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Pattern chat: docs-grounded LLM advisor for POST /patterns/{name}/chat.

One shared ADK Agent + Runner. The pattern's reference markdown lives in the
Session.state and is fetched via the ``read_pattern_doc`` tool; the agent's
instruction tells the LLM to call that tool before answering pattern-specific
questions. Sessions are keyed by (pattern_name, fe_session_id).
"""

from __future__ import annotations

import logging
import os
import time
from typing import AsyncIterator, Callable

import litellm
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from api.agentic_workflows.workflow_documentation import (
    load_parsed_workflow_documentation,
    workflow_name_to_documentation_slug,
)
from config.config import LLM_MODEL


logger = logging.getLogger(__name__)

APP_NAME = "pattern_chat"
DEFAULT_USER_ID = "pattern-chat-user"

STATE_KEY_MARKDOWN = "pattern_markdown"
STATE_KEY_PATTERN_NAME = "pattern_name"

SESSION_TTL_SECONDS = 30 * 60
MAX_EVICTIONS_PER_CALL = 10

# Injectable clock so tests can advance "time" without sleeping.
_clock: Callable[[], float] = time.monotonic

# (pattern_name::session_id) -> last-used monotonic timestamp.
_last_used: dict[str, float] = {}


_LITELLM_PROXY_BASE_URL = os.getenv("LITELLM_PROXY_BASE_URL")
_LITELLM_PROXY_API_KEY = os.getenv("LITELLM_PROXY_API_KEY")
if _LITELLM_PROXY_API_KEY and _LITELLM_PROXY_BASE_URL:
    os.environ["LITELLM_PROXY_API_KEY"] = _LITELLM_PROXY_API_KEY
    os.environ["LITELLM_PROXY_API_BASE"] = _LITELLM_PROXY_BASE_URL
    litellm.use_litellm_proxy = True


BASE_SYSTEM_PROMPT = (
    "You are the AGNTCY patterns advisor. The pattern in scope for this "
    "conversation is recorded in your session state; call the "
    "``read_pattern_doc`` tool to fetch its reference markdown before "
    "answering any question about the pattern's behaviour, structure, "
    "implementation, or trade-offs. Ground those answers in the returned "
    "material. Drawing on general agentic-systems knowledge is appropriate "
    "for follow-up implementation advice, but flag clearly when you go "
    "beyond the reference. Decline questions unrelated to agentic patterns.\n\n"
    "When the user asks about implementation details, code examples, "
    "repositories, demos, or how to get started building a pattern, "
    "delegate to the ``pattern_implementation_assistant``."
)

IMPLEMENTATION_ASSISTANT_PROMPT = (
    "You are the AGNTCY pattern implementation assistant. You help users "
    "get started building agentic patterns by pointing them to concrete "
    "repositories, demos, SDKs, etc.\n\n"
    "Do NOT hallucinate code, instead provide links, ask for follow-ups if needed.\n"
    "Call ``read_pattern_doc`` to understand which pattern is in scope "
    "before answering.\n\n"
    "## AGNTCY Core Pillars\n\n"
    "### Agent Directory Service\n"
    "Federated registry for cross-framework, cross-protocol, cross-registry "
    "agent discovery.\n"
    "- Docs: https://dir.agntcy.org/latest/\n"
    "- GitHub: https://github.com/agntcy/dir\n\n"
    "### SLIM\n"
    "A protocol that defines the standards and guidelines for secure and "
    "efficient network-level communication between AI agents.\n"
    "- Docs: https://slim.agntcy.org/latest/\n"
    "- GitHub: https://github.com/agntcy/slim\n\n"
    "### Observability\n"
    "Telemetry collectors, tools and services to enable multi-agent "
    "application observability and evaluation.\n"
    "- Docs: https://docs.agntcy.org/obs-and-eval/observe-and-eval/\n"
    "- GitHub: https://github.com/agntcy/docs\n\n"
    "### Identity\n"
    "Solution to manage and verify the identities of Agents or Tools "
    "issued by any organization, ensuring secure and trustworthy interactions.\n"
    "- Docs: https://docs.agntcy.org/identity/identity/\n"
    "- GitHub: https://github.com/agntcy/identity\n\n"
    "## Getting Involved\n"
    "- Slack: https://join.slack.com/t/agntcy/shared_invite/zt-3xozr6nzq-i6LXv2P8l2kVW4_Prnny2w\n"
    "- YouTube: https://www.youtube.com/playlist?list=PL49BrgsjXg5qVeRVqlX9O74W02q3c8fow\n\n"
    "## Guidelines\n"
    "- Link to specific AGNTCY pillar docs and repos when relevant to the pattern.\n"
    "- Relate implementation advice back to the pattern's reference doc.\n"
    "- If no AGNTCY resource exists for a topic, say so honestly and "
    "suggest general alternatives."
)


def read_pattern_doc(tool_context: ToolContext) -> str:
    """Return the reference markdown for the pattern currently in scope.

    Call this before answering questions about the pattern's behaviour,
    structure, implementation, or trade-offs.
    """
    return tool_context.state.get(STATE_KEY_MARKDOWN, "")


class PatternReferenceNotFound(Exception):
    """No reference markdown exists for the requested pattern name."""

    def __init__(self, pattern_name: str):
        self.pattern_name = pattern_name
        super().__init__(f"No reference material for pattern: {pattern_name}")


_session_service = InMemorySessionService()

_implementation_assistant = Agent(
    name="pattern_implementation_assistant",
    model=LiteLlm(model=LLM_MODEL),
    description=(
        "Helps users implement agentic patterns by linking to AGNTCY "
        "repositories, demos, SDKs, and code examples."
    ),
    instruction=IMPLEMENTATION_ASSISTANT_PROMPT,
    tools=[read_pattern_doc],
)

_root_agent = Agent(
    name="pattern_chat",
    model=LiteLlm(model=LLM_MODEL),
    description="Docs-grounded advisor for AGNTCY agentic patterns.",
    instruction=BASE_SYSTEM_PROMPT,
    tools=[read_pattern_doc],
    sub_agents=[_implementation_assistant],
)

_runner = Runner(agent=_root_agent, app_name=APP_NAME, session_service=_session_service)


def _session_key(pattern_name: str, fe_session_id: str) -> str:
    return f"{pattern_name}::{fe_session_id}"


async def _ensure_session(pattern_name: str, fe_session_id: str) -> None:
    """Create the ADK session and seed the pattern markdown if it doesn't exist."""
    sid = _session_key(pattern_name, fe_session_id)
    if await _session_service.get_session(
        app_name=APP_NAME, user_id=DEFAULT_USER_ID, session_id=sid
    ) is not None:
        return

    slug = workflow_name_to_documentation_slug(pattern_name)
    parsed = load_parsed_workflow_documentation(slug)
    if parsed is None:
        raise PatternReferenceNotFound(pattern_name)

    await _session_service.create_session(
        app_name=APP_NAME,
        user_id=DEFAULT_USER_ID,
        session_id=sid,
        state={
            STATE_KEY_MARKDOWN: parsed.full_markdown,
            STATE_KEY_PATTERN_NAME: pattern_name,
        },
    )


def _extract_text_chunks(event) -> list[str]:
    """Return the text payload(s) of a runner event, or [] for non-text events.

    Tool-call events (function_call) and tool-result events (function_response)
    are filtered out — the FE-visible stream only carries the model's text.
    """
    if event.get_function_calls() or event.get_function_responses():
        return []
    if not event.content or not event.content.parts:
        return []
    out: list[str] = []
    for part in event.content.parts:
        text = getattr(part, "text", None)
        if text:
            out.append(text)
    return out


async def _sweep_expired_sessions() -> None:
    """Drop sessions idle past SESSION_TTL_SECONDS; cap evictions per call."""
    now = _clock()
    expired = [
        sid for sid, last in _last_used.items()
        if now - last > SESSION_TTL_SECONDS
    ][:MAX_EVICTIONS_PER_CALL]
    for sid in expired:
        await _session_service.delete_session(
            app_name=APP_NAME, user_id=DEFAULT_USER_ID, session_id=sid
        )
        _last_used.pop(sid, None)


async def stream_one_turn(
    pattern_name: str,
    fe_session_id: str,
    user_message: str,
) -> AsyncIterator[str]:
    """Yield text chunks for one user turn. Raises PatternReferenceNotFound."""
    await _sweep_expired_sessions()
    await _ensure_session(pattern_name, fe_session_id)
    sid = _session_key(pattern_name, fe_session_id)
    _last_used[sid] = _clock()
    content = types.Content(role="user", parts=[types.Part(text=user_message)])

    # Forward partial chunks; fall back to the final non-partial when the model
    # didn't stream. Both together would double-render the answer.
    saw_partials = False
    async for event in _runner.run_async(
        user_id=DEFAULT_USER_ID,
        session_id=sid,
        new_message=content,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
    ):
        chunks = _extract_text_chunks(event)
        if not chunks:
            continue
        if event.partial:
            saw_partials = True
            for chunk in chunks:
                yield chunk
        elif not saw_partials:
            for chunk in chunks:
                yield chunk
