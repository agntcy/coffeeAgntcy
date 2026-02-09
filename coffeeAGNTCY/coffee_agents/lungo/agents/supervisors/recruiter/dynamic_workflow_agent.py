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

import httpx
from a2a.types import (
    Message,
    MessageSendParams,
    Role,
    SendMessageRequest,
    TextPart,
)
from a2a.utils.message import get_message_text
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.genai import types

from agents.supervisors.recruiter.models import (
    STATE_KEY_RECRUITED_AGENTS,
    STATE_KEY_SELECTED_AGENT_CIDS,
    STATE_KEY_TASK_MESSAGE,
    AgentRecord,
)


from config.config import (
    DEFAULT_MESSAGE_TRANSPORT, 
    TRANSPORT_SERVER_ENDPOINT,
)
from agntcy_app_sdk.semantic.a2a.protocol import A2AProtocol
from agents.supervisors.recruiter.shared import get_factory

logger = logging.getLogger("lungo.recruiter.supervisor.dynamic_workflow")

# Global factory and transport instances
factory = get_factory()
transport = factory.create_transport(
    DEFAULT_MESSAGE_TRANSPORT,
    endpoint=TRANSPORT_SERVER_ENDPOINT,
    name="default/default/dynamic_workflow_agent",
)


class DynamicWorkflowAgent(BaseAgent):
    """Executes tasks by sending messages to selected recruited agents via A2A HTTP.

    The root supervisor sets ``STATE_KEY_SELECTED_AGENT_CIDS`` in session state
    before transferring to this agent. This agent reads those CIDs, looks up the
    full records from ``STATE_KEY_RECRUITED_AGENTS``, and sends A2A messages
    directly via HTTP.
    """

    RESULT_STATE_PREFIX: ClassVar[str] = "dynamic_workflow_result_"

    async def _send_a2a_message(
        self, card: AgentRecord, message: str, agent_name: str
    ) -> str:
        """Send an A2A message to a remote agent and return the response text."""
        request_id = str(uuid4())
        message_id = str(uuid4())

        a2a_request = SendMessageRequest(
            id=request_id,
            params=MessageSendParams(
                message=Message(
                    messageId=message_id,
                    role=Role.user,
                    parts=[TextPart(text=message)],
                ),
            ),
        )

        logger.info(
            "[agent:dynamic_workflow] Sending A2A request to %s: %r",
            card.name,
            message[:100],
        )

        client = await factory.create_client(
            "A2A",
            agent_topic=A2AProtocol.create_agent_topic(card),
            transport=transport,
        )

        try:
            '''async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                response = await client.post(
                    url,
                    json=a2a_request.model_dump(mode="json", by_alias=True, exclude_none=True),
                )
                response.raise_for_status()
                data = response.json()'''
            
            response = await client.send_message(a2a_request)
            data = response.model_dump(mode="json", by_alias=True, exclude_none=True)

            # Extract text from A2A response using a2a.utils
            result = data.get("result", {})

            # Try to parse the response message and extract text
            # Format 1: result is a Message dict directly
            if "parts" in result and "messageId" in result:
                try:
                    response_message = Message.model_validate(result)
                    text = get_message_text(response_message)
                    if text:
                        return text
                except Exception:
                    logger.debug("Failed to parse result as Message", exc_info=True)

            # Format 2: result.status.message contains the Message
            status = result.get("status", {})
            status_message = status.get("message", {})
            if status_message and "parts" in status_message:
                try:
                    response_message = Message.model_validate(status_message)
                    text = get_message_text(response_message)
                    if text:
                        return text
                except Exception:
                    logger.debug("Failed to parse status.message as Message", exc_info=True)

            # Fallback: return raw result as string
            if result:
                return str(result)

            return f"Agent {agent_name} returned no response."

        except httpx.HTTPStatusError as e:
            logger.error(
                "[agent:dynamic_workflow] error from %s: %s",
                card.name,
                e.response.status_code,
            )
            return f"Error communicating with {agent_name}: HTTP {e.response.status_code}"
        except Exception as e:
            logger.error(
                "[agent:dynamic_workflow] Error sending to %s: %s",
                card.name,
                str(e),
                exc_info=True,
            )
            return f"Error communicating with {agent_name}: {str(e)}"

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        selected_cids: list[str] = ctx.session.state.get(
            STATE_KEY_SELECTED_AGENT_CIDS, []
        ) or []
        recruited: dict[str, dict] = ctx.session.state.get(
            STATE_KEY_RECRUITED_AGENTS, {}
        ) or {}
        task_message: str = ctx.session.state.get(STATE_KEY_TASK_MESSAGE, "") or ""

        logger.info(
            "[agent:dynamic_workflow] Running with selected_cids=%s, task=%r",
            selected_cids,
            task_message[:100] if task_message else "",
        )

        if not selected_cids:
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

        # Process each selected agent
        responses: list[str] = []

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

            '''if not record.url:
                logger.warning(
                    f"Agent {record.name} has no URL; skipping.",
                )
                responses.append(f"**{record.name}**: No URL configured for this agent.")
                continue'''

            logger.info(
                "[agent:dynamic_workflow] Sending to agent: %s at %s",
                record.name,
                record.url,
            )

            # Send A2A message
            response_text = await self._send_a2a_message(
                card=record,
                message=task_message,
                agent_name=record.name,
            )
            responses.append(f"**{record.name}**:\n{response_text}")

        # Combine responses
        if responses:
            combined = "\n\n---\n\n".join(responses)
        else:
            combined = "No agents were able to process the request."

        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=types.Content(
                role="model",
                parts=[types.Part(text=combined)],
            ),
        )

        # Clear the selection so it doesn't persist for the next turn
        ctx.session.state[STATE_KEY_SELECTED_AGENT_CIDS] = None
        ctx.session.state[STATE_KEY_TASK_MESSAGE] = None
