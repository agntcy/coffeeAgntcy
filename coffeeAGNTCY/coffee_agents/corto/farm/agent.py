# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from ioa_observe.sdk.decorators import agent, graph

from common.llm import get_llm

logger = logging.getLogger("corto.farm_agent.graph")

class State(TypedDict):
    prompt: str
    error_type: str
    error_message: str
    flavor_notes: str

@agent(name="farm_agent")
class FarmAgent:
    def __init__(self):
        self.FLAVOR_NODE = "FlavorNode"
        self._agent = self.build_graph()

    @graph(name="farm_graph")
    def build_graph(self) -> StateGraph:
        graph_builder = StateGraph(State)
        graph_builder.add_node(self.FLAVOR_NODE, self.flavor_node)
        graph_builder.add_edge(START, self.FLAVOR_NODE)
        graph_builder.add_edge(self.FLAVOR_NODE, END)
        return graph_builder.compile()

    async def flavor_node(self, state: State):
        """
        Generates a coffee flavor profile based on the user's prompt using an LLM.

        This method takes the current state (which includes a user prompt),
        sends it to a language model with a specialized system prompt, and returns
        a brief flavor description based on location and season.

        If the prompt doesn't contain enough context (e.g., missing location or season),
        it returns an error response instead of a profile.

        Args:
            state (State): The LangGraph state object containing a 'prompt' key with user input.

        Returns:
            dict: A dictionary with either:
                - "flavor_notes" (str): A brief tasting profile if valid context was extracted.
                - or an "error_type" and "error_message" if the input was insufficient.
        """
        # session_start()
        user_prompt = state.get("prompt")
        logger.debug(f"Received user prompt: {user_prompt}")

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
        logger.debug(f"LLM response: {flavor_notes}")
        if not flavor_notes.strip():
            logger.warning("Could not extract valid flavor notes from the user prompt.")
            return {
                "error_type": "invalid_input",
                "error_message": "Could not confidently extract coffee farm context from user prompt."
            }

        return {"flavor_notes": flavor_notes}

    async def ainvoke(self, input: str) -> dict:
        """
        Sends a user input string to the agent asynchronously and returns the result.

        Args:
            input (str): A user prompt describing a coffee farm, region, or condition.

        Returns:
            dict: A response dictionary, typically containing either:
                - "flavor_notes" with the LLM's generated profile, or
                - An error message if parsing or context extraction failed.
        """
        # build graph if not already built
        if not hasattr(self, '_agent'):
            self._agent = self.build_graph()
        return await self._agent.ainvoke({"prompt": input})