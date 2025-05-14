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

import logging
import uuid

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.prebuilt.chat_agent_executor import AgentState

from graph.node import send_message_node
from graph.router import exchange_node

class ExchangeGraph:
  def __init__(self):
    """
    Initialize the ExchangeGraph as a LangGraph.
    """
    self.graph = self.build_graph()

  def build_graph(self):
    """
    Build a LangGraph instance of the Exchange graph.

    Returns:
      CompiledGraph: A compiled LangGraph instance.
    """
    # Create the exchange node
    graph = StateGraph(AgentState)
    graph.add_edge(START, "Exchange")
    graph.add_node("Exchange", exchange_node)
    graph.add_node("SendMessageNode", send_message_node)
    graph.add_edge("SendMessageNode", END)

    checkpointer = InMemorySaver()
    return graph.compile(checkpointer=checkpointer)

  def get_graph(self):
    return self.graph

  async def serve(self, user_prompt: str):
    """
    Runs the LangGraph for exchange operations.

    Args:
      user_prompt str: user_prompt to serve.

    Returns:
      dict: Output data containing `agent_output`.
    """
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
