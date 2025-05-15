from typing import Any, Dict

from clients.a2a.client import send_message
from langchain_core.messages import AIMessage
from langgraph.prebuilt.chat_agent_executor import AgentState


def print_json_response(response: Any, description: str) -> None:
  """Helper function to print the JSON representation of a response."""
  print(f'--- {description} ---')
  if hasattr(response, 'root'):
    print(f'{response.root.model_dump_json(exclude_none=True)}\n')
  else:
    print(f'{response.model_dump(mode="json", exclude_none=True)}\n')

async def send_message_node(state: AgentState) -> Dict[str, Any]:
  """Graph node that sends a message to the A2A client and returns the response."""
  resp = await send_message(state["messages"][0].content)
  print_json_response(resp, 'Received A2A Response')

  return {
    "messages": [
      AIMessage(content="Successfully processed the coffee farm request.")
    ]
  }
