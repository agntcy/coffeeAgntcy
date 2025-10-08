# Shared imports for the module
import re
import uuid
import logging
from typing import Iterable
from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState, StateGraph, END
from ioa_observe.sdk.decorators import agent, graph
from agents.logistics.helpdesk.status_store.interface import OrderStatusStore
from agents.logistics.helpdesk.status_store.memory import InMemoryOrderStatusStore

logger = logging.getLogger("lungo.helpdesk.history_graph")
ORDER_ID_REGEX = re.compile(r"(?:order[_\s-]?id|order)\s*[:#=]\s*([A-Z0-9\-]{3,})", re.IGNORECASE)

class GraphState(MessagesState):
  """Graph state (single node workflow)."""
  pass

@agent(name="helpdesk_history_agent")
class HelpdeskHistoryGraph:
  """
  Single-node helpdesk agent that returns stored status history for an order id.
  Input prompt must contain something like: 'order id: ORDER-1234'
  """

  def __init__(self, store: OrderStatusStore | None = None):
    self.store = store or InMemoryOrderStatusStore()
    self.graph = self._build_graph()

  @staticmethod
  def _extract_order_id(text: str) -> str | None:
    if not text:
      return None
    m = ORDER_ID_REGEX.search(text)
    return m.group(1).upper() if m else None

  @staticmethod
  def _format_history(records: Iterable) -> str:
    lines = [
      f"{r.timestamp.isoformat()} | {r.agent} -> {r.status}"
      for r in sorted(records, key=lambda x: x.timestamp)
    ]
    return "\n".join(lines)

  async def _history_node(self, state: GraphState) -> dict:
    # Expect latest user message as last element (string or message object)
    raw = state["messages"]
    if isinstance(raw, list) and raw:
      user_text = str(raw[-1])
    else:
      user_text = str(raw)

    logger.info(f"HelpdeskHistoryGraph received input: {user_text}")

    order_id = self._extract_order_id(user_text)
    if not order_id:
      return {"messages": [AIMessage("No order id found. Provide one like 'order id: ORDER-1234'.")]}

    history = await self.store.get_history(order_id)
    if not history:
      return {"messages": [AIMessage(f"No history found for order {order_id}.")]}

    content = f"Order {order_id} history:\n{self._format_history(history)}"
    return {"messages": [AIMessage(content)]}

  @graph(name="helpdesk_history_graph")
  def _build_graph(self):
    workflow = StateGraph(GraphState)
    workflow.add_node("history", self._history_node)
    workflow.set_entry_point("history")
    workflow.add_edge("history", END)
    return workflow.compile()

  async def serve(self, prompt: str) -> str:
    if not isinstance(prompt, str) or not prompt.strip():
      raise ValueError("Prompt must be a non-empty string.")
    result = await self.graph.ainvoke(
      {"messages": [{"role": "user", "content": prompt}]},
      {"configurable": {"thread_id": uuid.uuid4()}}
    )
    messages = result.get("messages", [])
    for msg in reversed(messages):
      if isinstance(msg, AIMessage) and msg.content.strip():
        return msg.content.strip()
    return "No response generated."