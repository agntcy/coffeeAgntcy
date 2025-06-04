# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils.errors import ServerError
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

from agent import FarmAgent
from agent_executor import FarmAgent

logger = logging.getLogger("corto.farm_agent.a2a_executor")

class FarmAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = FarmAgent()

    def _validate_request(self, context: RequestContext) -> JSONRPCResponse | None:
        """Validates the incoming request."""
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
        Execute the agent's logic for a given request context.

        This method handles incoming message requests to generate a flavor profile for coffee beans.
        The agent should extract the necessary information from the `context`, invoke the FarmAgent
        to generate the flavor profile, and enqueue the response message to the `event_queue`.

        During execution, the agent may also publish `Task`, `Message`, `TaskStatusUpdateEvent`,
        or `TaskArtifactUpdateEvent` events. This method should return once the agent's execution
        for the current request is complete or yields control (e.g., enters an input-required state).

        Args:
            context: The request context containing the message, task ID, and other relevant data.
            event_queue: The queue to publish events to.
        """

        logger.info("Received message request: %s", context.message)

        validation_error = self._validate_request(context)
        if validation_error:
            event_queue.enqueue_event(validation_error)
            return
        
        prompt = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)
            event_queue.enqueue_event(task)

        try:
            output = await self.agent.ainvoke(prompt)
            if output.get("error_message") is not None and output.get("error_message") != "":
                logger.error("Error in agent response: %s", output.get("error_message"))
                message = new_agent_text_message(
                    output.get("error_message", "Failed to generate flavor profile"),
                )
                event_queue.enqueue_event(message)
                return

            flavor = output.get("flavor_notes", "No flavor profile returned")
            logger.info("Flavor profile generated: %s", flavor)
            event_queue.enqueue_event(new_agent_text_message(flavor))
        except Exception as e:
            logger.error(f'An error occurred while streaming the flavor profile response: {e}')
            raise ServerError(error=InternalError()) from e
        
    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        """Cancel this agent's execution for the given request context."""
        raise ServerError(error=UnsupportedOperationError())