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
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage

from common.llm import get_llm

class State(TypedDict):
    prompt: str
    error_type: str
    error_message: str
    flavor_notes: str


class FarmAgent:
    def __init__(self):
        graph_builder = StateGraph(State)
        graph_builder.add_node("FlavorNode", self.flavor_node)
        graph_builder.add_edge(START, "FlavorNode")
        graph_builder.add_edge("FlavorNode", END)
        self._agent = graph_builder.compile()

    async def flavor_node(self, state: State):
        """
        Generate a flavor profile for coffee beans based on user input by connecting to an LLM.
        
        Args:
            state (State): The current state containing the user prompt.
        Returns:
            dict: A dictionary containing the flavor notes or an error message if the input is invalid.        
        """
        user_prompt = state.get("prompt")

        system_prompt = (
            "You are a coffee farming expert and flavor profile connoisseur.\n"
            "The user will describe a question or scenario related to a coffee farm. "
            "Your job is to:\n"
            "1. Extract the `location` and `season` from the input if possible.\n"
            "2. Based on those, describe the expected **flavor profile** of the coffee grown there.\n"
            "3. Respond with only a brief, expressive flavor profile (1–3 sentences). "
            "Use tasting terminology like acidity, body, aroma, and finish.\n"
            "Respond with an empty response if no valid location or season is found. Do not include quotes or any placeholder."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = get_llm().invoke(messages)
        flavor_notes = response.content
        if not flavor_notes.strip():
            return {
                "error_type": "invalid_input",
                "error_message": "Could not confidently extract coffee farm context from user prompt."
            }

        return {"flavor_notes": flavor_notes}

    async def ainvoke(self, input: str) -> dict:
        """
        Asynchronously invoke the agent with the given input.
        Args:
            input (str): The user input to process.
        Returns:
            dict: The result of the agent's processing, containing flavor notes or an error message.
        """
        return await self._agent.ainvoke({"prompt": input})
