# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""ADK tool function that communicates with the remote recruiter A2A service
and persists results in session state."""

import asyncio
import json
import logging
from uuid import uuid4

import httpx
from a2a.client import ClientConfig, ClientFactory
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
from google.adk.tools.tool_context import ToolContext

from agents.supervisors.recruiter.models import (
    STATE_KEY_EVALUATION_RESULTS,
    STATE_KEY_RECRUITED_AGENTS,
    RecruitmentResponse,
)
from agents.supervisors.recruiter.recruiter_service_card import (
    RECRUITER_AGENT_CARD,
)

logger = logging.getLogger("lungo.recruiter.supervisor.recruiter_client")

# ---------------------------------------------------------------------------
# Side-channel queue for streaming A2A events to main.py
# ---------------------------------------------------------------------------
# The ADK runner blocks while a tool executes, so it cannot forward
# intermediate A2A events.  We use a module-level asyncio.Queue as a
# side-channel: recruit_agents pushes status dicts onto it and
# main.py's stream_generator drains it in parallel.
# ---------------------------------------------------------------------------

_a2a_event_queue: asyncio.Queue[dict | None] = asyncio.Queue()


def get_a2a_event_queue() -> asyncio.Queue[dict | None]:
    """Return the module-level queue that carries A2A streaming events."""
    return _a2a_event_queue


def _parse_dict_values(data: dict) -> dict[str, dict]:
    """Ensure all values are dicts, parsing JSON strings if needed.

    The recruiter service may return record values as JSON-encoded strings
    rather than parsed dicts.
    """
    result: dict[str, dict] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = value
        elif isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    result[key] = parsed
                else:
                    logger.warning("Value for key %s parsed to %s, not dict; skipping", key, type(parsed).__name__)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Value for key %s is not valid JSON; skipping", key)
        else:
            logger.warning("Unexpected value type %s for key %s; skipping", type(value).__name__, key)
    return result


def _extract_parts(parts: list[Part]) -> RecruitmentResponse:
    """Extract text, agent records, and evaluation results from A2A message parts."""
    text = None
    agent_records: dict[str, dict] = {}
    evaluation_results: dict[str, dict] = {}
    for part in parts:
        root = part.root
        if isinstance(root, TextPart):
            text = root.text
        elif isinstance(root, DataPart):
            meta_type = root.metadata.get("type") if root.metadata else None
            if meta_type == "found_agent_records":
                agent_records = _parse_dict_values(root.data)
            elif meta_type == "evaluation_results":
                evaluation_results = _parse_dict_values(root.data)
    return RecruitmentResponse(
        text=text,
        agent_records=agent_records,
        evaluation_results=evaluation_results,
    )


async def recruit_agents(query: str, tool_context: ToolContext) -> str:
    """Search the AGNTCY directory for agents matching a task description.

    Sends a streaming recruitment request to the remote recruiter A2A service
    and stores the discovered agent records in session state for later use by
    the DynamicWorkflowAgent.

    Args:
        query: Natural-language description of the task or capabilities needed.
        tool_context: Automatically injected by ADK; provides session state access.

    Returns:
        Human-readable summary of the recruitment results.
    """
    logger.info("[tool:recruit_agents] Called with query=%r", query)

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as httpx_client:
        config = ClientConfig(httpx_client=httpx_client, streaming=True)
        factory = ClientFactory(config)
        client = factory.create(RECRUITER_AGENT_CARD)

        message = Message(
            role=Role.user,
            message_id=str(uuid4()),
            parts=[Part(root=TextPart(text=query))],
        )

        response_data = RecruitmentResponse()

        async for event in client.send_message(message):
            # Streaming mode yields (Task, UpdateEvent) tuples
            if isinstance(event, tuple) and len(event) == 2:
                task, update = event

                # Forward intermediate status updates via the side-channel queue
                if isinstance(update, TaskStatusUpdateEvent) and not update.final:
                    if update.status and update.status.message:
                        parts = update.status.message.parts
                        if parts:
                            for p in parts:
                                if isinstance(p.root, TextPart) and p.root.text:
                                    status_text = p.root.text
                                    # Determine author from metadata
                                    author = None
                                    if update.status.message.metadata:
                                        author = update.status.message.metadata.get("author")
                                        if not author:
                                            author = update.status.message.metadata.get("from_agent")
                                    event_type = "a2a_status"
                                    if update.status.message.metadata:
                                        event_type = update.status.message.metadata.get("event_type", "a2a_status")

                                    logger.info(
                                        "[tool:recruit_agents] A2A status: %s (state=%s, final=%s)",
                                        status_text[:120],
                                        update.status.state if update.status else "?",
                                        update.final,
                                    )
                                    # Push to side-channel for main.py to pick up
                                    await _a2a_event_queue.put({
                                        "event_type": "status_update",
                                        "message": status_text,
                                        "state": "working",
                                        "author": author or "recruiter_service",
                                        "a2a_event_type": event_type,
                                    })

                # Extract final result from completed task
                if (
                    isinstance(task, Task)
                    and task.status
                    and task.status.state == TaskState.completed
                    and task.status.message
                ):
                    response_data = _extract_parts(task.status.message.parts)
            elif isinstance(event, Message):
                response_data = _extract_parts(event.parts)

        # Signal that A2A streaming is done for this tool invocation
        await _a2a_event_queue.put(None)

    # Merge into session state (preserve previously recruited agents)
    existing_agents = tool_context.state.get(STATE_KEY_RECRUITED_AGENTS, {})
    existing_agents.update(response_data.agent_records)
    tool_context.state[STATE_KEY_RECRUITED_AGENTS] = existing_agents

    existing_evals = tool_context.state.get(STATE_KEY_EVALUATION_RESULTS, {})
    existing_evals.update(response_data.evaluation_results)
    tool_context.state[STATE_KEY_EVALUATION_RESULTS] = existing_evals

    logger.info(
        "[tool:recruit_agents] Found %d agent(s), %d evaluation(s)",
        len(response_data.agent_records),
        len(response_data.evaluation_results),
    )

    # Build a human-readable summary
    if not response_data.agent_records:
        summary = response_data.text or "No agents found matching the query."
        logger.info("[tool:recruit_agents] Result: %s", summary)
        return summary

    summary_lines = [response_data.text or "Recruitment results:"]
    for cid, record in response_data.agent_records.items():
        name = record.get("name", "Unknown")
        desc = record.get("description", "")
        summary_lines.append(f"  - CID: {cid} | Name: {name} | {desc}")

    result = "\n".join(summary_lines)
    logger.info("[tool:recruit_agents] Result: %s", result)
    return result
