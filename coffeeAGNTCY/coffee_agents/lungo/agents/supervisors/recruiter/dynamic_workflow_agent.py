# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Dynamic Workflow Agent for the Recruiter Supervisor. This agent is responsible for managing
and orchestrating recruitment searches and evaluations through the agent recruiter service
and building dynamic workflows from the search results.

References:
https://dev.to/masahide/building-dynamic-parallel-workflows-in-google-adk-lmn
"""

import logging
from typing import AsyncGenerator, ClassVar

from google.adk.agents import BaseAgent, ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.events.event import Event
from google.genai import types

from agents.supervisors.recruiter.models import (
    STATE_KEY_RECRUITED_AGENTS,
    STATE_KEY_SELECTED_AGENT_CIDS,
    STATE_KEY_TASK_MESSAGE,
    AgentRecord,
)

logger = logging.getLogger("lungo.recruiter.supervisor.dynamic_workflow")


class DynamicWorkflowAgent(BaseAgent):
    """Creates and runs RemoteA2aAgent sub-agents for LLM-selected recruited agents.

    The root supervisor sets ``STATE_KEY_SELECTED_AGENT_CIDS`` in session state
    before transferring to this agent.  This agent reads those CIDs, looks up the
    full records from ``STATE_KEY_RECRUITED_AGENTS``, and dynamically instantiates
    ``RemoteA2aAgent`` instances to execute the task.

    Key design constraints (from the dev.to article pattern):
    - Fresh agent instances per invocation (ADK single-parent rule).
    - Unique names with ``run_id`` suffix to avoid collisions.
    - ``ClassVar`` for constants (ADK agents are Pydantic models).
    """

    RESULT_STATE_PREFIX: ClassVar[str] = "dynamic_workflow_result_"

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        selected_cids: list[str] = ctx.session.state.get(
            STATE_KEY_SELECTED_AGENT_CIDS, []
        )
        recruited: dict[str, dict] = ctx.session.state.get(
            STATE_KEY_RECRUITED_AGENTS, {}
        )
        task_message: str = ctx.session.state.get(STATE_KEY_TASK_MESSAGE, "")

        if not selected_cids:
            logger.warning("No agent CIDs selected for delegation.")
            yield Event(
                author=self.name,
                invocation_id=ctx.invocation_id,
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text="No agents were selected for delegation. "
                            "Please recruit agents first, then select which ones to use."
                        )
                    ],
                ),
            )
            return

        # Build RemoteA2aAgent instances for each selected CID
        run_id = ctx.invocation_id[:8]
        remote_agents: list[RemoteA2aAgent] = []
        cleanup_clients: list[RemoteA2aAgent] = []

        for cid in selected_cids:
            record_data = recruited.get(cid)
            if not record_data:
                logger.warning(f"CID {cid} not found in recruited agents; skipping.")
                continue

            try:
                record = AgentRecord(cid=cid, **record_data)
            except Exception:
                logger.warning(
                    f"Failed to parse agent record for CID {cid}; skipping.",
                    exc_info=True,
                )
                continue

            agent_card = record.to_agent_card()
            unique_name = f"{record.to_safe_agent_name()}_{run_id}"

            remote_agent = RemoteA2aAgent(
                name=unique_name,
                description=record.description or f"Remote agent {record.name}",
                agent_card=agent_card,
            )
            remote_agents.append(remote_agent)
            cleanup_clients.append(remote_agent)

        if not remote_agents:
            yield Event(
                author=self.name,
                invocation_id=ctx.invocation_id,
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text="None of the selected agent CIDs matched any recruited agents."
                        )
                    ],
                ),
            )
            return

        try:
            # Single agent: run directly. Multiple: wrap in ParallelAgent.
            if len(remote_agents) == 1:
                executor = remote_agents[0]
            else:
                executor = ParallelAgent(
                    name=f"parallel_executor_{run_id}",
                    sub_agents=remote_agents,
                )

            # Inject the task message into the conversation for the remote agent(s)
            if task_message:
                ctx.session.events.append(
                    Event(
                        author="user",
                        invocation_id=ctx.invocation_id,
                        content=types.Content(
                            role="user",
                            parts=[types.Part(text=task_message)],
                        ),
                    )
                )

            async for event in executor.run_async(ctx):
                yield event
        finally:
            # Cleanup httpx clients created by RemoteA2aAgent
            for ra in cleanup_clients:
                try:
                    if hasattr(ra, "_client") and ra._client is not None:
                        await ra._client.aclose()
                except Exception:
                    logger.debug(
                        f"Error closing client for {ra.name}", exc_info=True
                    )

            # Clear the selection so it doesn't persist for the next turn
            ctx.session.state.pop(STATE_KEY_SELECTED_AGENT_CIDS, None)
            ctx.session.state.pop(STATE_KEY_TASK_MESSAGE, None)
