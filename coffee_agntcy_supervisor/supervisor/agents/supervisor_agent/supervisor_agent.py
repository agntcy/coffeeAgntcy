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

from langchain.prompts import PromptTemplate
from langgraph_supervisor import create_supervisor

from supervisor.common.llm import get_llm

# Define the prompt template
template = """
You are a supervisor responsible for managing and analyzing farm data.
Your primary task is to check which farm has a yield and provide accurate responses based on the available data.
Follow these instructions carefully:

1. **Farm Data Analysis**:
   - If a farm is mentioned in the prompt, verify its yield status using the provided tools or data.
   - If no yield data is available for the farm, return an error message indicating the absence of yield information.
   - If yield data is available, provide the yield details clearly and concisely.

2. **General Instructions**:
   - Only use the tools and data provided to you.
   - If a farm is not found in the data, return an error message to the caller.
   - Ensure all responses are accurate and relevant to the query.

3. **Special Cases**:
   - If the prompt includes multiple farms, check the yield status for each farm individually and provide a summary.
   - If additional context is required to determine the yield, request clarification from the caller.

{additional_context}
"""

# Create the PromptTemplate instance
system_prompt = PromptTemplate(
    input_variables=["additional_context"],
    template=template
)

# from .state import AgentState

class SupervisorAgent:
    def __init__(self):
        self.name = "acorda_supervisor"
        self.tools = []
        self.agents = []
        self.prompt = (system_prompt.format(additional_context=""))

    def agent(self):
        graph = create_supervisor(
            supervisor_name=self.name,
            tools=self.tools,
            agents=self.agents,
            model=get_llm(),
            prompt=self.prompt,
            add_handoff_back_messages=True,
            output_mode="full_history",
        )

        return graph
