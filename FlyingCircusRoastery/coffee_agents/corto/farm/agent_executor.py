from uuid import uuid4

from a2a.server.agent_execution import BaseAgentExecutor
from a2a.server.events import EventQueue
from a2a.types import (Message, MessageSendParams, Part, Role,
                       SendMessageRequest, Task, TextPart)
from agent import FarmAgent  # Import message_node
from agent_executor import FarmAgent
from langchain_core.messages import HumanMessage
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
        input_data = self._parse_structured_input(params)

        if not input_data:
            message = self._error_message("Expected structured input with 'season' and 'location'.")
        else:
            try:
                output = await self.agent.ainvoke(input_data)
                flavor = output.get("flavor_notes", "No flavor profile returned.")
                message = self._build_message(flavor)
            except Exception as e:
                message = self._error_message(f"Failed to generate flavor profile: {e}")

        event_queue.enqueue_event(message)

    def _parse_structured_input(self, params: MessageSendParams) -> dict | None:
        metadata = params.message.metadata or {}
        if "season" in metadata and "location" in metadata:
            return metadata
        return None

    def _build_message(self, text: str) -> Message:
        return Message(
            role=Role.agent,
            parts=[Part(TextPart(text=text))],
            messageId=str(uuid4()),
        )

    def _error_message(self, msg: str) -> Message:
        return Message(
            role=Role.agent,
            parts=[Part(TextPart(text=f"[Error] {msg}"))],
            messageId=str(uuid4()),
        )
