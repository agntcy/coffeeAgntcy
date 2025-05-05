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

from typing import Annotated, Any, Dict, List, TypedDict

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph.message import add_messages


# Define the graph state
class GraphState(TypedDict):
  """
  Represents the state of the graph, containing a list of messages and a
  gateway holder.
  """

  messages: Annotated[List[BaseMessage], add_messages]

def node_remote_agp_fake(state: GraphState) -> Dict[str, Any]:
  """
  Mocked version of node_remote_agp for testing coffee farm purposes.

  Args:
      state (GraphState): The current graph state containing messages.

  Returns:
      Dict[str, Any]: A mocked response with a predefined message.
  """
  if not state["messages"]:
    return {"messages": [AIMessage(content="Mocked Error: No messages related to coffee farm in state")]}

  # Mocked response
  return {
    "messages": [
      AIMessage(content="Successfully processed the coffee farm request.")
    ]
  }
