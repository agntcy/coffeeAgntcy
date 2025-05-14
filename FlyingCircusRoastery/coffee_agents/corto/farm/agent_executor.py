import asyncio

from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4
from langchain_core.messages import HumanMessage
from agent import FarmAgent  # Import message_node
from typing_extensions import override
from agent_executor import FarmAgent
from a2a.server.agent_execution import BaseAgentExecutor
from a2a.server.events import EventQueue
from a2a.types import (
    Message,
    Part,
    Role,
    SendMessageRequest,
    Task,
    TextPart,
)


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
        user_input = request.message.parts[0].text
        inputs = {"messages": [HumanMessage(content=user_input)]}
        output = await self.agent.ainvoke(inputs)
        result = output["messages"][-1]

        message: Message = Message(
            role=Role.agent,
            parts=[Part(TextPart(text=result))],
            messageId=str(uuid4()),
        )
        event_queue.enqueue_event(message)
