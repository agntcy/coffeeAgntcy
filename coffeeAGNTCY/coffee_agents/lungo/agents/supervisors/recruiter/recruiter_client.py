# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""ADK tool function that communicates with the remote recruiter A2A service
and persists results in session state."""

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
                agent_records = root.data
            elif meta_type == "evaluation_results":
                evaluation_results = root.data
    return RecruitmentResponse(
        text=text,
        agent_records=agent_records,
        evaluation_results=evaluation_results,
    )


async def recruit_agents(query: str, tool_context: ToolContext) -> str:
    """Search the AGNTCY directory for agents matching a task description.

    Sends a recruitment request to the remote recruiter A2A service and stores
    the discovered agent records in session state for later use by the
    DynamicWorkflowAgent.

    Args:
        query: Natural-language description of the task or capabilities needed.
        tool_context: Automatically injected by ADK; provides session state access.

    Returns:
        Human-readable summary of the recruitment results.
    """
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as httpx_client:
        config = ClientConfig(httpx_client=httpx_client, streaming=False)
        factory = ClientFactory(config)
        client = factory.create(RECRUITER_AGENT_CARD)

        message = Message(
            role=Role.user,
            message_id=str(uuid4()),
            parts=[Part(root=TextPart(text=query))],
        )

        response_data = RecruitmentResponse()

        async for response in client.send_message(message):
            if isinstance(response, Message):
                response_data = _extract_parts(response.parts)
            elif isinstance(response, tuple) and len(response) == 2:
                task, _update = response
                if (
                    isinstance(task, Task)
                    and task.status.state == TaskState.completed
                    and task.status.message
                ):
                    response_data = _extract_parts(task.status.message.parts)

    # Merge into session state (preserve previously recruited agents)
    existing_agents = tool_context.state.get(STATE_KEY_RECRUITED_AGENTS, {})
    existing_agents.update(response_data.agent_records)
    tool_context.state[STATE_KEY_RECRUITED_AGENTS] = existing_agents

    existing_evals = tool_context.state.get(STATE_KEY_EVALUATION_RESULTS, {})
    existing_evals.update(response_data.evaluation_results)
    tool_context.state[STATE_KEY_EVALUATION_RESULTS] = existing_evals

    # Build a human-readable summary
    if not response_data.agent_records:
        return response_data.text or "No agents found matching the query."

    summary_lines = [response_data.text or "Recruitment results:"]
    for cid, record in response_data.agent_records.items():
        name = record.get("name", "Unknown")
        desc = record.get("description", "")
        summary_lines.append(f"  - CID: {cid} | Name: {name} | {desc}")

    return "\n".join(summary_lines)
