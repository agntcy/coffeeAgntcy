from typing import TypedDict

from langgraph.constants import END, START
from langgraph.graph import StateGraph
from farm.card import AGENT_CARD
from .nodes import FarmContact

class State(TypedDict):
    input_payload: dict
    output: dict

class ExchangeGraph:
  def __init__(self):
    """Initialize the ExchangeGraph as a LangGraph."""
    self.graph = self.build_graph()

  def build_graph(self):
    """Build a LangGraph instance of the Exchange graph."""

    farm_contact = FarmContact(AGENT_CARD)

    graph = StateGraph(State)
    graph.add_node("SendMessageNode", farm_contact.invoke)
    graph.add_edge(START, "SendMessageNode")
    graph.add_edge("SendMessageNode", END)

    return graph.compile()

  def get_graph(self):
    return self.graph

  async def serve(self, input_payload: dict):
    """Runs the LangGraph for exchange operations."""
    try:
      result = await self.graph.ainvoke({
          "input_payload": input_payload
      })
      return result["output"]
    except Exception as e:
      #TODO: change this
      raise Exception("operation failed: " + str(e))
