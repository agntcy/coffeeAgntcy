# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

from a2a.helpers import new_text_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils.errors import (
    ContentTypeNotSupportedError,
    InternalError,
    UnsupportedOperationError,
)
from farm.agent import FarmAgent

logger = logging.getLogger("corto.farm_agent.a2a_executor")


class FarmAgentExecutor(AgentExecutor):
    """
    This class extends the base `AgentExecutor` and executes requests on behalf of the Farm
    Agent in an Agent-to-Agent (A2A) architecture.

    This executor handles user prompts related to coffee farming and generates flavor profiles
    using a language model. It validates incoming requests, interacts with the FarmAgent for
    flavor generation, and publishes appropriate events (e.g., messages) to the event queue.

    """

    def __init__(self):
        self.agent = FarmAgent()

    def _validate_request(self, context: RequestContext) -> None:
        """
        Validates the incoming request context.

        Ensures that the context contains a valid message with content parts.

        Args:
            context (RequestContext): The incoming request context to validate.

        Raises:
            ContentTypeNotSupportedError: If the request has no message parts.
        """
        if not context or not context.message or not context.message.parts:
            logger.error("Invalid request parameters: %s", context)
            raise ContentTypeNotSupportedError()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Processes a user prompt to generate a coffee flavor profile via the FarmAgent.

        This method extracts the user prompt from the request context, invokes the FarmAgent
        asynchronously to get a flavor profile, and publishes the result as a single final
        message. If the prompt is invalid or processing fails, it returns an error message.

        Args:
            context (RequestContext): The request context containing message metadata.
            event_queue (EventQueue): The queue used to emit events (messages).

        Raises:
            ContentTypeNotSupportedError: If the request has no message parts.
            InternalError: If an unexpected error occurs during flavor generation.
        """

        logger.info("Received message request: %s", context.message)

        self._validate_request(context)

        prompt = context.get_user_input()
        if not prompt:
            logger.warning("Empty or missing prompt in user input.")
            await event_queue.enqueue_event(
                new_text_message("No valid input prompt provided.")
            )
            return

        try:
            output = await self.agent.ainvoke(prompt)
            if (
                output.get("error_message") is not None
                and output.get("error_message") != ""
            ):
                logger.error("Error in agent response: %s", output.get("error_message"))
                message = new_text_message(
                    output.get("error_message", "Failed to generate flavor profile"),
                )
                await event_queue.enqueue_event(message)
                return

            flavor = output.get("flavor_notes", "No flavor profile returned")
            logger.info("Flavor profile generated: %s", flavor)
            await event_queue.enqueue_event(new_text_message(flavor))
        except Exception as e:
            logger.error(
                f"An error occurred while streaming the flavor profile response: {e}"
            )
            raise InternalError() from e

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> None:
        """
        Cancel this agent's execution for the given request context.

        Args:
            request (RequestContext): The request to cancel.
            event_queue (EventQueue): The event queue to potentially emit cancellation events.

        Raises:
            UnsupportedOperationError: Always raised due to unsupported operation.
        """
        raise UnsupportedOperationError()
