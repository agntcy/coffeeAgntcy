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
from langgraph.constants import END, START

from supervisor.agents.supervisor_agent.supervisor_agent import SupervisorAgent
# from supervisor.clients.agp_client.agp_client import node_remote_agp #TODO: Use this
from supervisor.clients.agp_client.mock import \
    node_remote_agp_fake  # TODO: Delete this after the AGP client is implemented


class SupervisorGraph:
  def __init__(self):
    """
    Initialize the SupervisorGraph as a LangGraph.
    """
    self.graph = self.build_graph()

  def build_graph(self):
    """
    Build a LangGraph instance of the Supervisor graph.

    Returns:
      CompiledGraph: A compiled LangGraph instance.
    """
    graph = SupervisorAgent().agent()

    graph.add_node("node_agp_boardcast", node_remote_agp_fake) # TODO: Use node_remote_agp
    graph.add_edge(START, "node_agp_boardcast")
    graph.add_edge("node_agp_boardcast", END)

    checkpointer = InMemorySaver()
    return graph.compile(checkpointer=checkpointer)

  def get_graph(self):
    return self.graph

  def serve(self, user_prompt: str):
    """
    Runs the LangGraph for supervisor operations.

    Args:
      user_prompt str: user_prompt to serve.

    Returns:
      dict: Output data containing `agent_output`.
    """
    try:
      logging.info("got user prompt: " + user_prompt)
      result = self.graph.invoke({
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
