# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Dynamic Workflow Agent for the Recruiter Supervisor. This agent is responsible for managing
and orchestrating recruitment searches and evaluations through the agent recruiter service
and building dynamic workflows from the search results.
"""

import logging
from typing import AsyncGenerator, ClassVar
from uuid import uuid4
from a2a.types import (
    AgentCard,
    Message,
    Role,
    TextPart,
)
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.genai import types

from agents.supervisors.recruiter.models import (
    STATE_KEY_RECRUITED_AGENTS,
    STATE_KEY_SELECTED_AGENT,
    STATE_KEY_TASK_MESSAGE,
    AgentProtocol,
    AgentRecord,
)
from agents.supervisors.recruiter.recruiter_client import (
    _event_consumer,
    _event_interceptor,
)
from agents.supervisors.recruiter.shared import a2a_client_factory
from common.workflow_registry import (
    make_tool_call_context,
    register_workflow,
    workflow_names,
)

WorkflowNames = workflow_names()

logger = logging.getLogger("lungo.recruiter.supervisor.dynamic_workflow")

class DynamicWorkflowAgent(BaseAgent):
    """Executes tasks by sending messages to selected recruited agents via A2A HTTP.

    The root supervisor sets ``STATE_KEY_SELECTED_AGENT_CIDS`` in session state
    before transferring to this agent. This agent reads those CIDs, looks up the
    full records from ``STATE_KEY_RECRUITED_AGENTS``, and sends A2A messages
    directly via HTTP.
    """

    RESULT_STATE_PREFIX: ClassVar[str] = "dynamic_workflow_result_"

    @register_workflow(WorkflowNames.ON_DEMAND_DISCOVERY)
    async def _send_a2a_message(
        self, card: AgentCard, message: str, agent_name: str
    ) -> str:
        """Send an A2A message to a remote agent and return the response text."""
        message_id = str(uuid4())

        a2a_message = Message(
            messageId=message_id,
            role=Role.user,
            parts=[TextPart(text=message)],
        )

        logger.info(
            "[agent:dynamic_workflow] Sending A2A request to %s: %r",
            card.name,
            message[:100],
        )

        # negotiate and create the client based on the card's preferred transport
        client = await a2a_client_factory.create(
            card,
            interceptors=[_event_interceptor],
            consumers=[_event_consumer],
        )

        try:
            result_text = None
            ctx = make_tool_call_context(DynamicWorkflowAgent._send_a2a_message)
            async for response in client.send_message(a2a_message, context=ctx):
                logger.info(
                    "[agent:dynamic_workflow] Response received from %s: %s",
                    agent_name,
                    response,
                )

                if isinstance(response, Message):
                    for part in response.parts:
                        part_root = part.root
                        if hasattr(part_root, "text"):
                            result_text = part_root.text.strip()
                elif isinstance(response, tuple):
                    task_update, event = response
                    if (
                        hasattr(task_update, "status")
                        and task_update.status
                        and task_update.status.message
                    ):
                        for part in task_update.status.message.parts:
                            part_root = part.root
                            if hasattr(part_root, "text"):
                                result_text = part_root.text.strip()

            if result_text:
                return result_text

            return f"Agent {agent_name} returned no response."

        except Exception as e:
            logger.error(
                "[agent:dynamic_workflow] Error sending to %s: %s",
                card.name,
                str(e),
                exc_info=True,
            )
            return f"Error communicating with {agent_name}: {str(e)}"

    @staticmethod
    def _protocol_from_record(record: AgentRecord) -> AgentProtocol:
        """Determine the protocol to use based on the agent record."""
        return record.protocol

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        selected_cid: str | None = ctx.session.state.get(STATE_KEY_SELECTED_AGENT)
        recruited: dict[str, dict] = ctx.session.state.get(
            STATE_KEY_RECRUITED_AGENTS, {}
        ) or {}
        task_message: str = ctx.session.state.get(STATE_KEY_TASK_MESSAGE, "") or ""

        logger.info(
            "[agent:dynamic_workflow] Running with selected_cid=%s, task=%r",
            selected_cid,
            task_message[:100] if task_message else "",
        )

        if not selected_cid:
            logger.warning("[agent:dynamic_workflow] No agent CIDs selected for delegation.")
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

        # Process the selected agent
        record_data = recruited.get(selected_cid)
        if not record_data:
            logger.warning(f"CID {selected_cid} not found in recruited agents.")
            yield Event(
                author=self.name,
                invocation_id=ctx.invocation_id,
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=f"Selected agent (CID: {selected_cid[:20]}...) not found in recruited agents."
                        )
                    ],
                ),
            )
            return

        try:
            record = AgentRecord(cid=selected_cid, **record_data)
        except Exception:
            logger.warning(
                f"Failed to parse agent record for CID {selected_cid}.",
                exc_info=True,
            )
            yield Event(
                author=self.name,
                invocation_id=ctx.invocation_id,
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=f"Failed to parse agent record for selected agent."
                        )
                    ],
                ),
            )
            return

        protocol = self._protocol_from_record(record)
        if protocol != AgentProtocol.A2A:
            logger.error(
                "[agent:dynamic_workflow] Unsupported protocol %r for agent %s. "
                "Only A2A agents are currently supported.",
                protocol.value,
                record.name,
            )
            yield Event(
                author=self.name,
                invocation_id=ctx.invocation_id,
                content=types.Content(
                    # ADK reuses google.genai types; "model" = responder role
                    # (Google's equivalent of "assistant")
                    role="model",
                    parts=[
                        types.Part(
                            text=f"Agent '{record.name}' uses unsupported protocol "
                            f"'{protocol.value}'. Only A2A agents are currently supported."
                        )
                    ],
                ),
            )
            return

        agent_card = record.to_agent_card()

        logger.info(
            "[agent:dynamic_workflow] Sending to agent: %s at %s",
            record.name,
            record.url,
        )

        # Send A2A message
        response_text = await self._send_a2a_message(
            card=agent_card,
            message=task_message,
            agent_name=record.name,
        )
        combined = f"**{record.name}**:\n{response_text}"

        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=types.Content(
                role="model",
                parts=[types.Part(text=combined)],
            ),
        )

        # Clear the selection so it doesn't persist for the next turn
        ctx.session.state[STATE_KEY_TASK_MESSAGE] = None
