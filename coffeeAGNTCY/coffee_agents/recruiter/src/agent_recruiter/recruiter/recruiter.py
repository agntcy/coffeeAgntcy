# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Optional, AsyncGenerator
from contextlib import aclosing
import os
from agent_recruiter.common.logging import get_logger

from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.events.event import Event as AdkEvent
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
from agent_recruiter.common.llm import configure_llm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agent_recruiter.common.agent_utils import call_agent_async

from agent_recruiter.agent_registries import create_registry_search_agent
from agent_recruiter.interviewers import create_evaluation_agent
from agent_recruiter.plugins import (
    ToolCachePlugin,
    CacheConfig,
    load_cache_config,
    DEFAULT_EXCLUDED_TOOLS,
)

logger = get_logger("recruiter.recruiter")

configure_llm()

# ============================================================================
# Recruiter Agent Configuration
# ============================================================================

session_service = InMemorySessionService()

async def get_or_create_session(
    app_name: str, 
    user_id: str, 
    session_id: str
):
    """Retrieve an existing session or create a new one.

    This prevents AlreadyExistsError on repeated agent invocations.
    """

    session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if session is not None:
        logger.info(f"✅ Retrieved existing session '{session_id}' for user '{user_id}'.")
        return session
    
    # Define initial state data
    initial_state = {
        "user_preference_agent_registry": "AGNTCY Directory Service",
        "found_agent_records": {},  # Initialize empty dict for agent records from searches
        "evaluation_criteria": [],  # Initialize empty list for evaluation criteria
        "evaluation_results": {}   # Initialize empty dict for evaluation results
    }

    session_stateful = await session_service.create_session(
        app_name=app_name, # Use the consistent app name
        user_id=user_id,
        session_id=session_id,
        state=initial_state # <<< Initialize state during creation
    )

    logger.info(f"✅ Session '{session_id}' created for user '{user_id}'.")

    # Verify the initial state was set correctly
    retrieved_session = await session_service.get_session(app_name=app_name,
            user_id=user_id,
            session_id = session_id)
    
    assert retrieved_session is not None, "Session retrieval failed."
    return session_stateful

# ============================================================================
# Agent Execution Functions
# ============================================================================

AGENT_INSTRUCTION = """You are the main Recruiter Agent coordinating a team.

You have specialized sub-agents:
- registry_search_agent: Finds agents in registries and directories based on user queries.
- agent_evaluator: Runs agentic interviews and evaluations on agents based on user-defined scenarios.

How to handle requests:
- If the user asks to find or search for agents or skills: delegate to the registry_search_agent
- If the user asks to EVALUATE, INTERVIEW, or assess agents: delegate to the agent_evaluator
- For anything else: respond appropriately or state you cannot handle it
"""

def create_recruiter_agent(sub_agents) -> Agent:
    """Create and configure the Recruiter Agent."""

    LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o")

    root_agent = Agent(
        name="RecruiterAgent",
        model=LiteLlm(model=LLM_MODEL),
        description="The main coordinator agent. Handles recruiter tasks and delegates specialized queries to sub-agents.",
        instruction=AGENT_INSTRUCTION,
        sub_agents=sub_agents,
    )

    return root_agent

class RecruiterTeam:
    """Multi-agent team for agent recruitment with configurable caching.

    Caching can be configured via environment variables:
        CACHE_ENABLED: Enable/disable all caching ("true"/"false")
        CACHE_MODE: "model", "tool", "both", or "none"

        MODEL_CACHE_TTL: Model cache TTL in seconds
        MODEL_CACHE_MAX_ENTRIES: Model cache max entries

        TOOL_CACHE_TTL: Tool cache TTL in seconds
        TOOL_CACHE_MAX_ENTRIES: Tool cache max entries
        TOOL_CACHE_TOOLS: Comma-separated tool names or "all"
    """

    def __init__(
        self,
        app_name: str = "agent_recruiter",
        cache_config: Optional[CacheConfig] = None
    ):
        """Create necessary agents and runner.

        Args:
            app_name: Application name for session management.
            cache_config: Optional cache configuration. If None, loads from
                         environment variables via load_cache_config().
        """
        self.app_name = app_name

        # Load cache config from env vars if not provided
        self._cache_config = cache_config or load_cache_config()

        # ================================================================
        # Phase 1: Initialize Specialized Sub-Agents
        # ================================================================
        
        # create a registry search agent which can search, pull, and filter agents
        registry_search_agent = create_registry_search_agent()

        # create an evaluation agent which can evaluate agents based on policies
        evaluation_agent = create_evaluation_agent()

        sub_agents = [registry_search_agent, evaluation_agent]

        # ================================================================
        # Phase 2: Assemble Main Coordinator Agent
        # ================================================================
        # Build the primary recruiter agent that orchestrates sub-agent delegation
        # and manages the overall recruitment workflow
        root_agent_stateful = create_recruiter_agent(sub_agents)
        self.root_agent = root_agent_stateful

        # ================================================================
        # Phase 3: Configure Plugins for Caching and Optimization
        # ================================================================
        plugins = []
        self._tool_cache_plugin: Optional[ToolCachePlugin] = None

        if self._cache_config.tool_cache_enabled:
            # Use configured excluded tools or default set
            excluded_tools = self._cache_config.tool.excluded_tools or DEFAULT_EXCLUDED_TOOLS

            self._tool_cache_plugin = ToolCachePlugin(
                ttl_seconds=self._cache_config.tool.ttl_seconds,
                max_entries=self._cache_config.tool.max_entries,
                excluded_tools=excluded_tools,
                enabled=True
            )
            plugins.append(self._tool_cache_plugin)
            logger.info(
                f"Tool cache enabled (ttl={self._cache_config.tool.ttl_seconds}s, "
                f"max_entries={self._cache_config.tool.max_entries}, "
                f"excluded_tools={excluded_tools})"
            )

        if not plugins:
            logger.info("Caching disabled (CACHE_MODE=none or CACHE_ENABLED=false)")
        else:
            logger.info(f"Total plugins enabled: {len(plugins)}")

        # ================================================================
        # Phase 4: Initialize Execution Runtime
        # ================================================================
        # Create the runner that manages agent execution, session state,
        # and plugin lifecycle for the complete recruitment workflow
        runner_root_stateful = Runner(
            agent=root_agent_stateful,
            app_name=self.app_name,
            session_service=session_service,
            plugins=plugins
        )

        self.runner = runner_root_stateful

    def get_root_agent(self) -> Agent:
        """Get the root recruiter agent."""
        return self.root_agent

    async def get_found_agent_records(self, user_id: str, session_id: str) -> dict[str, dict]:
        """Retrieve agent records stored in session state by the registry search agent.

        Args:
            user_id: User ID for the session
            session_id: Session ID to retrieve state from

        Returns:
            Dict of agent records keyed by CID, or empty dict if none found
        """
        session = await session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        if session is None:
            logger.warning(f"[get_found_agent_records] Session '{session_id}' not found for user '{user_id}'")
            return {}

        records = session.state.get("found_agent_records", {})
        logger.info(
            f"[get_found_agent_records] session_id={session_id} -> {len(records)} records: {list(records.keys())}"
        )
        return records

    async def get_evaluation_results(self, user_id: str, session_id: str) -> dict[str, dict]:
        """Retrieve evaluation results stored in session state by the agent evaluator.

        Args:
            user_id: User ID for the session
            session_id: Session ID to retrieve state from

        Returns:
            Dict of evaluation results keyed by agent_id, or empty dict if none found.
            Also includes a "_summary" key with overall evaluation summary.
        """
        session = await session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        if session is None:
            logger.warning(f"Session '{session_id}' not found for user '{user_id}'")
            return {}

        return session.state.get("evaluation_results", {})

    async def clear_evaluation_results(self, user_id: str, session_id: str) -> bool:
        """Clear the evaluation results from session state.

        Args:
            user_id: User ID for the session
            session_id: Session ID to clear state from

        Returns:
            True if cleared successfully, False if session not found
        """
        session = await session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        if session is None:
            logger.warning(f"Session '{session_id}' not found for user '{user_id}'")
            return False

        session.state["evaluation_results"] = {}
        logger.info(f"Cleared evaluation results for session '{session_id}'")
        return True


    async def invoke(self, user_message: str, user_id: str, session_id: str) -> dict:
        """Process a user message and return the agent response with any found records.

        Returns:
            Dict containing:
                - response: The text response from the agent
                - found_agent_records: Dict of agent records found during the session
                - evaluation_results: Dict of evaluation results from the session
        """
        await get_or_create_session(app_name=self.app_name, user_id=user_id, session_id=session_id)

        response = await call_agent_async(user_message, self.runner, user_id, session_id)

        if not response.strip():
            raise RuntimeError("No valid response generated.")

        # Get any agent records that were found during this invocation
        found_records = await self.get_found_agent_records(user_id, session_id)

        # Get any evaluation results from this invocation
        evaluation_results = await self.get_evaluation_results(user_id, session_id)

        return {
            "response": response.strip(),
            "found_agent_records": found_records,
            "evaluation_results": evaluation_results,
        }

    async def stream(
        self,
        user_message: str,
        user_id: str,
        session_id: str
    ) -> AsyncGenerator[AdkEvent, None]:
        """Stream ADK events progressively instead of waiting for final result.

        This method enables real-time streaming of intermediate events such as
        tool calls, agent handoffs, and status updates.

        Args:
            user_message: The user's input message
            user_id: User ID for the session
            session_id: Session ID for state management

        Yields:
            ADK Event objects as they are produced by the agent
        """
        await get_or_create_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )

        content = types.Content(
            role='user',
            parts=[types.Part(text=user_message)]
        )

        run_config = RunConfig(streaming_mode=StreamingMode.SSE)

        logger.debug(f"Starting streaming execution: user_id={user_id}, session_id={session_id}")

        async with aclosing(
            self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
                run_config=run_config,
            )
        ) as event_stream:
            async for event in event_stream:
                logger.debug(f"Streaming event: author={event.author}, partial={event.partial}")
                yield event

    def get_cache_stats(self) -> dict:
        """Get cache statistics for tool cache.

        Returns:
            Dict with mode and tool_cache stats (None if disabled).
        """
        return {
            "mode": self._cache_config.mode.value,
            "tool_cache": (
                self._tool_cache_plugin.get_stats()
                if self._tool_cache_plugin else None
            ),
        }

    def get_tool_cache_stats(self) -> Optional[dict]:
        """Get tool cache statistics.

        Returns:
            Dict with cache stats, or None if tool caching is disabled.
        """
        if self._tool_cache_plugin is None:
            return None
        return self._tool_cache_plugin.get_stats()

    def clear_cache(self) -> dict:
        """Clear all caches.

        Returns:
            Dict with number of entries cleared from each cache.
        """
        return {
            "tool_cache_cleared": (
                self._tool_cache_plugin.clear()
                if self._tool_cache_plugin else 0
            ),
        }

    def clear_tool_cache(self) -> int:
        """Clear tool cache.

        Returns:
            Number of entries cleared, or 0 if tool caching is disabled.
        """
        if self._tool_cache_plugin is None:
            return 0
        return self._tool_cache_plugin.clear()

    def set_cache_enabled(self, enabled: bool) -> None:
        """Enable or disable tool caching at runtime.

        Args:
            enabled: Whether to enable caching.
        """
        if self._tool_cache_plugin is not None:
            self._tool_cache_plugin.set_enabled(enabled)