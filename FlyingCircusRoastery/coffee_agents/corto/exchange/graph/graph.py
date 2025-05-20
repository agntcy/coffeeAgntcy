from typing import TypedDict

from clients.a2a.client import send_message
from langgraph.constants import END, START
from langgraph.graph import StateGraph

class State(TypedDict):
    input_payload: dict
    output: dict

class ExchangeGraph:
  def __init__(self):
    """Initialize the ExchangeGraph as a LangGraph."""
    self.graph = self.build_graph()

  def build_graph(self):
    """Build a LangGraph instance of the Exchange graph."""
    graph = StateGraph(State)
    graph.add_node("SendMessageNode", self.send_message_node)
    graph.add_edge(START, "SendMessageNode")
    graph.add_edge("SendMessageNode", END)

    return graph.compile()

  def get_graph(self):
    return self.graph
  
  async def send_message_node(self, state: State):
    """Graph node that sends a message to the A2A client and returns the response."""
    resp = await send_message(state["input_payload"])
    return {"output": resp}

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
