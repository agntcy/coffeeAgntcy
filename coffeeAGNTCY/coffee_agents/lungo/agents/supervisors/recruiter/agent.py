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
    STATE_KEY_EVALUATION_RESULTS,
    STATE_KEY_RECRUITED_AGENTS,
    STATE_KEY_SELECTED_AGENT,
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

def _find_agent_by_name_or_cid(
    identifier: str, recruited: dict[str, dict]
) -> tuple[str | None, dict | None]:
    """Find an agent by name or CID from recruited agents.

    Args:
        identifier: Agent name (partial match) or CID (exact match)
        recruited: Dict of recruited agents keyed by CID

    Returns:
        Tuple of (cid, record) if found, (None, None) if not found
    """
    # First try exact CID match
    if identifier in recruited:
        return identifier, recruited[identifier]

    # Try case-insensitive name match
    identifier_lower = identifier.lower().strip()
    for cid, record in recruited.items():
        name = record.get("name", "").lower().strip()
        if name == identifier_lower:
            return cid, record
        # Partial match - identifier is contained in name
        if identifier_lower in name:
            return cid, record

    return None, None

async def clear_recruited_agents(tool_context: ToolContext) -> str:
    """Clear all recruited agents from session state.

    This can be used to reset the state if the user wants to start a new search
    or if there are too many agents stored from previous searches.

    Args:
        tool_context: Automatically injected by ADK.

    Returns:
        Confirmation message that recruited agents have been cleared.
    """
    logger.info("[tool:clear_recruited_agents] Called")
    tool_context.state[STATE_KEY_RECRUITED_AGENTS] = {}
    return "✓ Cleared all recruited agents from memory. You can start a new search now."

async def select_agent(
    agent_identifier: str, tool_context: ToolContext
) -> str:
    """Select a recruited agent by name or CID for conversation.

    Call this after recruit_agents has found suitable agents. Once selected,
    all subsequent messages will be forwarded directly to this agent until
    you call deselect_agent.

    Args:
        agent_identifier: The agent's name (e.g., "Shipping agent") or CID.
                         Name matching is case-insensitive and supports partial matches.
        tool_context: Automatically injected by ADK.

    Returns:
        Confirmation message with the selected agent's details.
    """
    logger.info("[tool:select_agent] Called with identifier=%r", agent_identifier)

    recruited = tool_context.state.get(STATE_KEY_RECRUITED_AGENTS, {})

    if not recruited:
        return (
            "No agents have been recruited yet. "
            "Please use recruit_agents to search for agents first."
        )

    cid, record = _find_agent_by_name_or_cid(agent_identifier, recruited)

    if not cid or not record:
        # List available agents
        available = [
            f"  - {r.get('name', 'Unknown')} (CID: {c[:20]}...)"
            for c, r in recruited.items()
        ]
        available_list = "\n".join(available) if available else "  (none)"
        return (
            f"No agent found matching '{agent_identifier}'.\n\n"
            f"Available agents:\n{available_list}\n\n"
            "Please provide the exact name or CID of an agent from the list above."
        )

    # Store the selected agent CID
    tool_context.state[STATE_KEY_SELECTED_AGENT] = cid

    agent_name = record.get("name", "Unknown")
    agent_desc = record.get("description", "No description available")

    logger.info(
        "[tool:select_agent] Selected agent: name=%s, cid=%s",
        agent_name,
        cid[:20],
    )

    return (
        f"✓ Selected **{agent_name}**\n\n"
        f"Description: {agent_desc}\n\n"
        f"You can now send messages directly to this agent. "
        f"Use 'deselect agent' when you're done to return to the supervisor."
    )


async def deselect_agent(tool_context: ToolContext) -> str:
    """Deselect the current agent and return to supervisor mode.

    Call this when you want to stop talking to the currently selected agent
    and return to the recruiter supervisor for searching or selecting a different agent.

    Args:
        tool_context: Automatically injected by ADK.

    Returns:
        Confirmation that no agent is selected.
    """
    logger.info("[tool:deselect_agent] Called")

    current = tool_context.state.get(STATE_KEY_SELECTED_AGENT)
    recruited = tool_context.state.get(STATE_KEY_RECRUITED_AGENTS, {})

    if current:
        record = recruited.get(current, {})
        agent_name = record.get("name", current[:20])
        tool_context.state[STATE_KEY_SELECTED_AGENT] = None  # Clear selection
        logger.info("[tool:deselect_agent] Deselected agent: %s", agent_name)
        return f"✓ Deselected **{agent_name}**. You are now back in supervisor mode."
    else:
        return "No agent was selected. You are in supervisor mode."


async def send_to_agent(
    message: str, tool_context: ToolContext
) -> str:
    """Send a message to the currently selected agent.

    This tool forwards your message to the selected agent for processing.
    You must have an agent selected via select_agent first.

    Args:
        message: The message to send to the selected agent.
        tool_context: Automatically injected by ADK.

    Returns:
        Instruction to transfer to the dynamic_workflow sub-agent.
    """
    logger.info("[tool:send_to_agent] Called with message=%r", message[:100] if message else "")

    selected_cid = tool_context.state.get(STATE_KEY_SELECTED_AGENT)

    if not selected_cid:
        return (
            "No agent is currently selected. "
            "Please use select_agent first to choose an agent to talk to."
        )

    recruited = tool_context.state.get(STATE_KEY_RECRUITED_AGENTS, {})
    record = recruited.get(selected_cid, {})
    agent_name = record.get("name", selected_cid[:20])

    # Set up state for dynamic_workflow_agent
    tool_context.state[STATE_KEY_TASK_MESSAGE] = message

    logger.info(
        "[tool:send_to_agent] Forwarding to agent: %s, message: %r",
        agent_name,
        message[:50],
    )

    return (
        f"Forwarding message to **{agent_name}**. "
        f"Transfer to the 'dynamic_workflow' sub-agent now."
    )


# ---------------------------------------------------------------------------
# Sub-agents
# ---------------------------------------------------------------------------

dynamic_workflow_agent = DynamicWorkflowAgent(
    name="dynamic_workflow",
    description=(
        "Executes tasks by forwarding messages to the selected remote agent. "
        "Transfer to this agent AFTER calling send_to_agent."
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
from the AGNTCY directory and connect them to selected agents.

**Tools:**
1. `recruit_agents(query)` — Search for agents. Pass the user's FULL message as the query.

2. `select_agent(agent_identifier)` — Select an agent by name or CID.
   Example: select_agent("Shipping agent") or select_agent("baeabc123...")

3. `deselect_agent()` — Clear the current selection and return to supervisor mode.

4. `send_to_agent(message)` — Forward a message to the selected agent. After this,
   transfer to the 'dynamic_workflow' sub-agent.

5. `clear_recruited_agents()` — Clear all recruited agents from memory to reset state.

**Sub-agent:**
- `dynamic_workflow` — Executes the actual communication with the selected agent.
  Only transfer here AFTER calling send_to_agent.

**Workflow:**

1. **SEARCH requests** (user says "find", "search", "recruit", "look for"):
   → Call `recruit_agents` with the full user message
   → Present results with names and CIDs

2. **SELECT requests** (user says "select", "choose", "use", "talk to" + agent name/CID):
   → Call `select_agent` with the identifier
   → Confirm selection

3. **DESELECT requests** (user says "deselect", "clear", "back", "stop talking"):
   → Call `deselect_agent`

4. **MESSAGE to selected agent** (any other message when an agent is selected):
   → Call `send_to_agent` with the user's message
   → Transfer to `dynamic_workflow`

5. **No agent selected and not a search/select request**:
   → Ask the user to either search for agents or select one from previous results

6. **CLEAR state** (user says "clear all", "reset all", "remove all agents"):
   → Call `clear_recruited_agents` to clear memory of recruited agents

**IMPORTANT:**
- When an agent is selected, forward ALL non-command messages to that agent
- The user talks to ONE agent at a time
- Always show available agents after a search so the user can select by name""",
    tools=[recruit_agents, select_agent, deselect_agent, send_to_agent, clear_recruited_agents],
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


def _log_event(event: Event) -> None:
    """Log key details from an ADK event for observability."""
    author = getattr(event, "author", "?")
    is_final = event.is_final_response()

    # Extract text snippet from content
    text_snippet = ""
    if event.content and event.content.parts:
        for part in event.content.parts:
            if hasattr(part, "text") and part.text:
                text_snippet = part.text[:120]
                break
            if hasattr(part, "function_call") and part.function_call:
                text_snippet = f"function_call: {part.function_call.name}({dict(part.function_call.args) if part.function_call.args else {}})"
                break
            if hasattr(part, "function_response") and part.function_response:
                text_snippet = f"function_response: {part.function_response.name}"
                break

    tag = "FINAL" if is_final else "event"
    logger.info("[%s] author=%s | %s", tag, author, text_snippet)


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


async def get_recruited_agents(user_id: str, session_id: str) -> dict[str, dict]:
    """Retrieve agent records stored in session state by recruit_agents tool.

    Args:
        user_id: User ID for the session
        session_id: Session ID to retrieve state from

    Returns:
        Dict of agent records keyed by CID, or empty dict if none found
    """
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if session is None:
        logger.warning("Session '%s' not found for user '%s'", session_id, user_id)
        return {}
    return session.state.get(STATE_KEY_RECRUITED_AGENTS, {})


async def get_evaluation_results(user_id: str, session_id: str) -> dict[str, dict]:
    """Retrieve evaluation results stored in session state.

    Args:
        user_id: User ID for the session
        session_id: Session ID to retrieve state from

    Returns:
        Dict of evaluation results keyed by agent_id, or empty dict if none found
    """
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if session is None:
        logger.warning("Session '%s' not found for user '%s'", session_id, user_id)
        return {}
    return session.state.get(STATE_KEY_EVALUATION_RESULTS, {})


async def get_selected_agent(user_id: str, session_id: str) -> dict | None:
    """Retrieve the currently selected agent from session state.

    Args:
        user_id: User ID for the session
        session_id: Session ID to retrieve state from

    Returns:
        Dict with agent info (cid, name, description) or None if no agent selected
    """
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if session is None:
        return None

    selected_cid = session.state.get(STATE_KEY_SELECTED_AGENT)
    if not selected_cid:
        return None

    recruited = session.state.get(STATE_KEY_RECRUITED_AGENTS, {})
    record = recruited.get(selected_cid, {})

    return {
        "cid": selected_cid,
        "name": record.get("name", "Unknown"),
        "description": record.get("description", ""),
    }


async def call_agent(
    query: str, user_id: str = "default_user", session_id: str | None = None
) -> dict:
    """Send a query to the recruiter supervisor and return a structured response.

    Args:
        query: The user's message.
        user_id: User identifier for session management.
        session_id: Optional session ID for multi-turn conversations.
            If None, a new session is created.

    Returns:
        Dict containing:
            - response: The text response from the agent
            - session_id: The session ID used
            - agent_records: Dict of recruited agent records (keyed by CID)
            - evaluation_results: Dict of evaluation results (keyed by agent_id)
    """
    if session_id is None:
        session_id = str(uuid4())

    logger.info("[call_agent] session_id=%s query=%r", session_id, query)
    await _get_or_create_session(user_id, session_id)

    content = types.Content(role="user", parts=[types.Part(text=query)])

    final_response = "Agent did not produce a final response."

    async for event in root_runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        _log_event(event)
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
            break

    # Retrieve structured data from session state
    agent_records = await get_recruited_agents(user_id, session_id)
    evaluation_results = await get_evaluation_results(user_id, session_id)
    selected_agent = await get_selected_agent(user_id, session_id)

    logger.info("[call_agent] Final response: %s", final_response[:200])
    logger.info(
        "[call_agent] agent_records=%d, evaluation_results=%d, selected_agent=%s",
        len(agent_records),
        len(evaluation_results),
        selected_agent.get("name") if selected_agent else None,
    )

    return {
        "response": final_response,
        "session_id": session_id,
        "agent_records": agent_records,
        "evaluation_results": evaluation_results,
        "selected_agent": selected_agent,
    }


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

    logger.info("[stream_agent] session_id=%s query=%r", session_id, query)
    await _get_or_create_session(user_id, session_id)

    content = types.Content(role="user", parts=[types.Part(text=query)])

    async for event in root_runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        _log_event(event)
        yield event, session_id
