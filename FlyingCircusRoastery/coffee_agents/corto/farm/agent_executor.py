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
    """Test AgentProxy Implementation."""

    def __init__(self):
        self.agent = FarmAgent()

    @override
    async def on_message_send(
            self,
            request: SendMessageRequest,
            event_queue: EventQueue,
            task: Task | None,
    ) -> None:
        params: MessageSendParams = request.params
        query = self._get_user_query(params)

        inputs = {"messages": [HumanMessage(content=query)]}
        output = await self.agent.ainvoke(inputs)
        result = output["messages"][-1]

        message: Message = Message(
            role=Role.agent,
            parts=[Part(TextPart(text=result.content))],
            messageId=str(uuid4()),
        )

        event_queue.enqueue_event(message)

    def _get_user_query(self, task_send_params: MessageSendParams) -> str:
        """Helper to get user query from task send params."""
        part = task_send_params.message.parts[0].root
        if not isinstance(part, TextPart):
            raise ValueError('Only text parts are supported')
        return part.text
