import logging
import uuid

from graph.node import send_message_node
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.prebuilt.chat_agent_executor import AgentState


class ExchangeGraph:
  def __init__(self):
    """Initialize the ExchangeGraph as a LangGraph."""
    self.graph = self.build_graph()

  def build_graph(self):
    """Build a LangGraph instance of the Exchange graph."""

    graph = StateGraph(AgentState)
    graph.add_edge(START, "SendMessageNode")
    graph.add_node("SendMessageNode", send_message_node)
    graph.add_edge("SendMessageNode", END)

    checkpointer = InMemorySaver()
    return graph.compile(checkpointer=checkpointer)

  def get_graph(self):
    return self.graph

  async def serve(self, user_prompt: str):
    """Runs the LangGraph for exchange operations."""
    try:
      result = await self.graph.ainvoke({
        "messages": [
          {
            "role": "user",
            "content": user_prompt
          }
        ],
      }, {"configurable": {"thread_id": uuid.uuid4()}})

      if logging.getLogger().isEnabledFor(logging.DEBUG):
        for m in result["messages"]:
          m.pretty_print()

      return result["messages"][-1].content, result

    except Exception as e:
      raise Exception("operation failed: " + str(e))
