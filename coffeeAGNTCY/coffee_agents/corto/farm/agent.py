import os
from typing import TypedDict

from cisco_outshift_agent_utils.llm_factory import LLMFactory
from langgraph.graph import END, START, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage

from config.config import LLM_PROVIDER


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
        user_prompt = state.get("prompt")

        system_prompt = (
            "You are a coffee farming expert and flavor profile connoisseur.\n"
            "The user will describe a question or scenario related to a coffee farm. "
            "Your job is to:\n"
            "1. Extract the `location` and `season` from the input if possible.\n"
            "2. Based on those, describe the expected **flavor profile** of the coffee grown there.\n"
            "3. Respond with only a brief, expressive flavor profile (1–3 sentences). "
            "Use tasting terminology like acidity, body, aroma, and finish.\n"
            # "If no meaningful location or season is found, respond with an empty string." # Commented out to allow for error handling
        )

        llm = LLMFactory(provider=LLM_PROVIDER).get_llm()
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = llm.invoke(messages)
        flavor_notes = response.content
        if flavor_notes == "":
            return {
                "error_type": "invalid_input",
                "error_message": "Could not confidently extract coffee farm context from user prompt."
            }

        return {"flavor_notes": flavor_notes}

    async def ainvoke(self, input: str) -> dict:
        return await self._agent.ainvoke({"prompt": input})
