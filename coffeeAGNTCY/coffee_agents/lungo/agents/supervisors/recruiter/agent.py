# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Recruiter Supervisor Agent Module

Root ADK supervisor agent that:
1. Recruits agents from the AGNTCY directory via the recruit_agents tool
2. Selects and delegates tasks to recruited agents via DynamicWorkflowAgent
3. Maintains session state of previously recruited agents for multi-turn flows
"""

import logging
import os
from typing import AsyncGenerator
from uuid import uuid4

import litellm
from google.adk.agents import Agent
from google.adk.events.event import Event
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from config.config import LLM_MODEL

from agents.supervisors.recruiter.dynamic_workflow_agent import (
    DynamicWorkflowAgent,
)
from agents.supervisors.recruiter.models import (
    STATE_KEY_RECRUITED_AGENTS,
    STATE_KEY_SELECTED_AGENT_CIDS,
    STATE_KEY_TASK_MESSAGE,
)
from agents.supervisors.recruiter.recruiter_client import recruit_agents

logger = logging.getLogger("lungo.recruiter.supervisor.agent")

# ---------------------------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------------------------

LITELLM_PROXY_BASE_URL = os.getenv("LITELLM_PROXY_BASE_URL")
LITELLM_PROXY_API_KEY = os.getenv("LITELLM_PROXY_API_KEY")

if LITELLM_PROXY_API_KEY and LITELLM_PROXY_BASE_URL:
    os.environ["LITELLM_PROXY_API_KEY"] = LITELLM_PROXY_API_KEY
    os.environ["LITELLM_PROXY_API_BASE"] = LITELLM_PROXY_BASE_URL
    logger.info(f"Using LiteLLM Proxy: {LITELLM_PROXY_BASE_URL}")
    litellm.use_litellm_proxy = True
else:
    logger.info("Using direct LLM instance")

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


async def select_and_delegate(
    agent_cids: list[str], task_message: str, tool_context: ToolContext
) -> str:
    """Select recruited agents by CID and prepare for task delegation.

    Call this after recruit_agents has found suitable agents. Provide the CIDs
    of the agents you want to delegate the task to and the task message to send.

    Args:
        agent_cids: List of agent CIDs to delegate the task to.
        task_message: The task or question to send to the selected agents.
        tool_context: Automatically injected by ADK.

    Returns:
        Confirmation text. After this tool returns, transfer to the
        ``dynamic_workflow`` sub-agent to execute the delegation.
    """
    recruited = tool_context.state.get(STATE_KEY_RECRUITED_AGENTS, {})

    # Validate that all CIDs exist
    valid_cids = [cid for cid in agent_cids if cid in recruited]
    invalid_cids = [cid for cid in agent_cids if cid not in recruited]

    if invalid_cids:
        logger.warning(f"Invalid CIDs ignored: {invalid_cids}")

    if not valid_cids:
        return (
            "None of the provided CIDs match recruited agents. "
            "Please run recruit_agents first, then use the CIDs from the results."
        )

    tool_context.state[STATE_KEY_SELECTED_AGENT_CIDS] = valid_cids
    tool_context.state[STATE_KEY_TASK_MESSAGE] = task_message

    agent_names = [
        recruited[cid].get("name", cid) for cid in valid_cids
    ]
    return (
        f"Selected {len(valid_cids)} agent(s) for delegation: {', '.join(agent_names)}. "
        f"Now transfer to the 'dynamic_workflow' sub-agent to execute the task."
    )


# ---------------------------------------------------------------------------
# Sub-agents
# ---------------------------------------------------------------------------

dynamic_workflow_agent = DynamicWorkflowAgent(
    name="dynamic_workflow",
    description=(
        "Executes tasks using previously recruited agents. Transfer to this "
        "agent AFTER calling select_and_delegate to run the selected agents. "
        "Do NOT call this agent directly — use select_and_delegate first."
    ),
)

# ---------------------------------------------------------------------------
# Root Supervisor Agent
# ---------------------------------------------------------------------------

root_agent = Agent(
    name="recruiter_supervisor",
    model=LiteLlm(model=LLM_MODEL),
    description="The main recruiter supervisor agent that finds and delegates tasks to agents.",
    instruction="""You are a Recruiter Supervisor agent. Your job is to help users find agents
from the AGNTCY directory and delegate tasks to them.

You have two tools and one sub-agent:

**Tools:**
1. `recruit_agents(query)` — Search the AGNTCY directory for agents matching a task
   description. Use this when the user wants to find or discover agents. The results
   are stored in your session state so you can reference them later.

2. `select_and_delegate(agent_cids, task_message)` — Select one or more previously
   recruited agents by their CID and prepare a task message for them. Use this when
   the user wants to execute a task using a recruited agent.

**Sub-agent:**
- `dynamic_workflow` — After calling select_and_delegate, transfer to this sub-agent
  to actually execute the task on the selected remote agents.

**Workflow:**
1. When the user asks to find/search/recruit agents: call `recruit_agents` with their query.
   Present the results clearly, including agent names, CIDs, and descriptions.

2. When the user wants to use a recruited agent for a task:
   a. Call `select_and_delegate` with the appropriate CID(s) and task message.
   b. Then transfer to the `dynamic_workflow` sub-agent.

3. If the user asks to execute a task but no agents have been recruited yet,
   first recruit agents, then select and delegate.

Always present CIDs when showing recruitment results so the user can reference them.""",
    tools=[recruit_agents, select_and_delegate],
    sub_agents=[dynamic_workflow_agent],
)

# ---------------------------------------------------------------------------
# Session & Runner
# ---------------------------------------------------------------------------

APP_NAME = "recruiter_supervisor"
session_service = InMemorySessionService()
root_runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)

# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


async def _get_or_create_session(user_id: str, session_id: str):
    """Retrieve an existing session or create a new one."""
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if session is None:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
    return session


async def call_agent(
    query: str, user_id: str = "default_user", session_id: str | None = None
) -> tuple[str, str]:
    """Send a query to the recruiter supervisor and return (response_text, session_id).

    Args:
        query: The user's message.
        user_id: User identifier for session management.
        session_id: Optional session ID for multi-turn conversations.
            If None, a new session is created.

    Returns:
        Tuple of (final_response_text, session_id).
    """
    if session_id is None:
        session_id = str(uuid4())

    await _get_or_create_session(user_id, session_id)

    content = types.Content(role="user", parts=[types.Part(text=query)])

    final_response = "Agent did not produce a final response."

    async for event in root_runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
            break

    return final_response, session_id


async def stream_agent(
    query: str, user_id: str = "default_user", session_id: str | None = None
) -> AsyncGenerator[tuple[Event, str], None]:
    """Stream events from the recruiter supervisor.

    Args:
        query: The user's message.
        user_id: User identifier for session management.
        session_id: Optional session ID for multi-turn conversations.

    Yields:
        Tuples of (event, session_id).
    """
    if session_id is None:
        session_id = str(uuid4())

    await _get_or_create_session(user_id, session_id)

    content = types.Content(role="user", parts=[types.Part(text=query)])

    async for event in root_runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        yield event, session_id
