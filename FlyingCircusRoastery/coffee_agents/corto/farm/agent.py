import os
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from openai import OpenAI, AzureOpenAI


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
            "If no meaningful location or season is found, respond with an empty string."
        )

        response = execute_openai_prompt(system_prompt, user_prompt)

        flavor_notes = response.choices[0].message.content.strip()
        if flavor_notes == "":
            return {
                "error_type": "invalid_input",
                "error_message": "Could not confidently extract coffee farm context from user prompt."
            }

        return {"flavor_notes": flavor_notes}

    async def ainvoke(self, input: str) -> dict:
        return await self._agent.ainvoke({"prompt": input})


def execute_openai_prompt(system_prompt: str, user_prompt: str):
    if os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        try:
            return client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
        except Exception as e:
            print(f"Error encountered while calling Azure OpenAI: {e}")
            return ""

    elif os.getenv("OPENAI_API_KEY"):
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        try:
            return client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
        except Exception as e:
            print(f"Error encountered while calling OpenAI: {e}")
            return ""
    else:
        raise EnvironmentError("No valid OpenAI or Azure OpenAI credentials found in environment.")
