# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Message, Part, Role
from a2a.utils.errors import (
    ContentTypeNotSupportedError,
    InternalError,
    UnsupportedOperationError,
)

from agents.farms.colombia.agent import FarmAgent
from agents.farms.colombia.card import AGENT_CARD
from common.a2a_helpers import message_metadata
from common.workflow_context_prop import workflow_context_scope

logger = logging.getLogger("longo.colombia_farm_agent.agent_executor")


class FarmAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = FarmAgent()

    def _validate_request(self, context: RequestContext) -> None:
        """Validates the incoming request."""
        if not context or not context.message or not context.message.parts:
            logger.error("Invalid request parameters: %s", context)
            raise ContentTypeNotSupportedError()

    @staticmethod
    def _read_workflow_identity(
        context: RequestContext,
    ) -> tuple[str | None, str | None]:
        """Extract workflow identity propagated in the A2A message metadata.

        The supervisor stamps workflow_name/workflow_instance_id so MCP
        tool-call events emitted by this farm correlate to the same workflow
        instance the user is observing.
        """
        metadata = message_metadata(getattr(context, "message", None))
        workflow_name = metadata.get("workflow_name")
        workflow_instance_id = metadata.get("workflow_instance_id")
        return (
            workflow_name if isinstance(workflow_name, str) else None,
            workflow_instance_id if isinstance(workflow_instance_id, str) else None,
        )

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Execute the agent's logic for a given request context.

        This method handles incoming message requests to generate a yield estimate for coffee beans.
        The agent should extract the necessary information from the `context`, invoke the FarmAgent
        to generate the yield estimate in lb, and enqueue the response message to the `event_queue`.

        The reply is a single final `Message`. This method returns once the agent's
        execution for the current request is complete.

        Args:
            context: The request context containing the message, task ID, and other relevant data.
            event_queue: The queue to publish events to.
        """

        logger.debug("Received message request: %s", context.message)

        self._validate_request(context)

        prompt = context.get_user_input()

        workflow_name, workflow_instance_id = self._read_workflow_identity(context)

        try:
            if workflow_name or workflow_instance_id:
                # Baggage is the primary identity channel; the explicit kwargs
                # are an in-process fallback the MCP wrapper uses if baggage is
                # ever unavailable inside the graph run.
                with workflow_context_scope(
                    workflow_name=workflow_name,
                    workflow_instance_id=workflow_instance_id,
                ):
                    output = await self.agent.ainvoke(
                        prompt,
                        workflow_name=workflow_name,
                        workflow_instance_id=workflow_instance_id,
                    )
            else:
                output = await self.agent.ainvoke(prompt)

            message = Message(
                message_id=str(uuid4()),
                role=Role.ROLE_AGENT,
                metadata={"name": AGENT_CARD.name},
                parts=[Part(text=output)],
            )

            logger.info("agent output message: %s", message)

            await event_queue.enqueue_event(message)
        except Exception as e:
            logger.error(
                f"An error occurred while streaming the yield estimate response: {e}"
            )
            raise InternalError() from e

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> None:
        """Cancel this agent's execution for the given request context."""
        raise UnsupportedOperationError()
