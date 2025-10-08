# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    UnsupportedOperationError,
    JSONRPCResponse,
    ContentTypeNotSupportedError,
    InternalError,
    Task)
from a2a.utils import (
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError

from farm.agent import FarmAgent

logger = logging.getLogger("corto.farm_agent.a2a_executor")

class FarmAgentExecutor(AgentExecutor):
    """
    This class extends the base `AgentExecutor` and executes requests on behalf of the Farm 
    Agent in an Agent-to-Agent (A2A) architecture.

    This executor handles user prompts related to coffee farming and generates flavor profiles
    using a language model. It validates incoming requests, interacts with the FarmAgent for 
    flavor generation, and publishes appropriate events (e.g., messages or tasks) to the event queue.

    """
    def __init__(self):
        self.agent = FarmAgent()

    def _validate_request(self, context: RequestContext) -> JSONRPCResponse | None:
        """
        Validates the incoming request context.

        Ensures that the context contains a valid message with content parts.
        If the request is invalid, returns an appropriate JSON-RPC error response.

        Args:
            context (RequestContext): The incoming request context to validate.

        Returns:
            JSONRPCResponse | None: An error response if validation fails, otherwise None.
        """
        if not context or not context.message or not context.message.parts:
            logger.error("Invalid request parameters: %s", context)
            return JSONRPCResponse(error=ContentTypeNotSupportedError())
        return None
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Processes a user prompt to generate a coffee flavor profile via the FarmAgent.

        This method extracts the user prompt from the request context, invokes the FarmAgent
        asynchronously to get a flavor profile, and publishes the result as an event.
        If the prompt is invalid or processing fails, it returns an error message.

        If no current task is associated with the request, a new task is created and emitted.

        Args:
            context (RequestContext): The request context containing message and task metadata.
            event_queue (EventQueue): The queue used to emit events (messages, tasks, etc.).

        Raises:
            ServerError: If an unexpected error occurs during flavor generation.
        """

        logger.info("Received message request: %s", context.message)

        validation_error = self._validate_request(context)
        if validation_error:
            await event_queue.enqueue_event(validation_error)
            return
        
        prompt = context.get_user_input()
        if not prompt:
            logger.warning("Empty or missing prompt in user input.")
            await event_queue.enqueue_event(
                new_agent_text_message("No valid input prompt provided.")
            )
            return
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        try:
            output = await self.agent.ainvoke(prompt)
            if output.get("error_message") is not None and output.get("error_message") != "":
                logger.error("Error in agent response: %s", output.get("error_message"))
                message = new_agent_text_message(
                    output.get("error_message", "Failed to generate flavor profile"),
                )
                await event_queue.enqueue_event(message)
                return

            flavor = output.get("flavor_notes", "No flavor profile returned")
            logger.info("Flavor profile generated: %s", flavor)
            await event_queue.enqueue_event(new_agent_text_message(flavor))
        except Exception as e:
            logger.error(f'An error occurred while streaming the flavor profile response: {e}')
            raise ServerError(error=InternalError()) from e
        
    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        """
        Cancel this agent's execution for the given request context.
        
        Args:
            request (RequestContext): The request to cancel.
            event_queue (EventQueue): The event queue to potentially emit cancellation events.

        Raises:
            ServerError: Always raised due to unsupported operation.
        """
        raise ServerError(error=UnsupportedOperationError())