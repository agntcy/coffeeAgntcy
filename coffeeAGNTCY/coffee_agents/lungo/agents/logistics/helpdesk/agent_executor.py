
import logging


from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    UnsupportedOperationError,
    Task,
)
from a2a.utils.errors import ServerError
from a2a.utils import new_agent_text_message
from agents.logistics.helpdesk.card import AGENT_CARD
from agents.logistics.helpdesk.status_store.memory import InMemoryOrderStatusStore
from agents.logistics.helpdesk.status_store.interface import OrderStatusStore

logger = logging.getLogger("lungo.helpdesk_agent.executor")

class HelpdeskAgent:
    def __init__(self, store: OrderStatusStore):
        self.store = store

    async def invoke(self, context: RequestContext) -> str:
        prompt = context.get_user_input()
        logger.info(f"HelpdeskAgent received prompt: {prompt}")

        # TODO: Implement actual logic to process the prompt and update order status
        # order_id = InMemoryOrderStatusStore.extract_order_id(prompt)
        # status = InMemoryOrderStatusStore.extract_status(prompt)
        # agent = InMemoryOrderStatusStore.extract_agent(prompt)
        # await self.store.record_status(order_id, agent, status)

        return f"{AGENT_CARD.name} IDLE"


class HelpdeskAgentExecutor(AgentExecutor):
    """Test AgentProxy Implementation."""

    def __init__(self, store: OrderStatusStore | None = None):
        self.store = store or InMemoryOrderStatusStore()
        self.agent = HelpdeskAgent(self.store)
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)

    async def execute(
            self,
            context: RequestContext,
            event_queue: EventQueue,
    ) -> None:
        await self.store.seed_fake_data()
        result = await self.agent.invoke(context)
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(
            self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        """Cancel this agent's execution for the given request context."""
        raise ServerError(error=UnsupportedOperationError())
