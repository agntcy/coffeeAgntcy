# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

from clients.a2a.client import send_message
from typing import Annotated, Any, Dict
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
  """
  Mocked version of node_remote_agp for testing coffee farm purposes.

  Args:
      state (GraphState): The current graph state containing messages.

  Returns:
      Dict[str, Any]: A mocked response with a predefined message.
  """

  resp = await send_message(state["messages"][0].content)

  print_json_response(resp, 'Received A2A Response')

  return {
    "messages": [
      AIMessage(content="Successfully processed the coffee farm request.")
    ]
  }