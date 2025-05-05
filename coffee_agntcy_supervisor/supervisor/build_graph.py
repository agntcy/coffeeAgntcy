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

from supervisor.graph.graph import SupervisorGraph


# Invoked from deploy_acp/acorda_agent.json manifest file for ACP
def build_graph():
  """
     Build a LangGraph instance of the Acorda workflow.

     Returns:
     CompiledGraph: A compiled LangGraph instance.
     """
  supervisor_graph = SupervisorGraph()
  return supervisor_graph.get_graph()


graph = build_graph()
