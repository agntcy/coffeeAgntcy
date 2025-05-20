from uuid import uuid4

from a2a.server.agent_execution import BaseAgentExecutor
from a2a.server.events import EventQueue
from a2a.types import (Message, Part, Role,
                       SendMessageRequest, Task, TextPart)
from agent import FarmAgent  # Import message_node
from agent_executor import FarmAgent
from typing_extensions import override


class FarmAgentExecutor(BaseAgentExecutor):
    def __init__(self):
        self.agent = FarmAgent()

    @override
    async def on_message_send(
            self,
            request: SendMessageRequest,
            event_queue: EventQueue,
            task: Task | None,
    ) -> None:
        print(f"Received message: {request.params}")

        params = request.params
        # add error handling for missing or invalid parameters
        if not params or not params.message or not params.message.parts:
            message = self._error_message("invalid_input", "Missing agent message")
            event_queue.enqueue_event(message)
            return

        prompt = params.message.parts[0].root.text
        try:
            output = await self.agent.ainvoke(prompt)
            if output.get("error_message") is not None and output.get("error_message") != "":
                message = self._error_message(
                    output.get("error_type", "internal_error"),
                    output.get("error_message", "Failed to generate flavor profile"),
                )
                event_queue.enqueue_event(message)
                return       
            flavor = output.get("flavor_notes", "No flavor profile returned")
            message = self._build_message(flavor)
        except Exception as e:
            print(f"Error during flavor profile generation: {e}")
            message = self._error_message("internal_error", "Failed to generate flavor profile")

        event_queue.enqueue_event(message)

    def _build_message(self, text: str) -> Message:
        return Message(
            role=Role.agent,
            parts=[Part(TextPart(text=text))],
            messageId=str(uuid4()),
        )

    def _error_message(self, code: str, msg: str) -> Message:
        return Message(
            role=Role.agent,
            parts=[Part(TextPart(text=f"{code}: {msg}"))],
            messageId=str(uuid4()),
        )
