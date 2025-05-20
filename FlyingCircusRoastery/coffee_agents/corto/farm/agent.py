import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from openai import OpenAI, AzureOpenAI

class State(TypedDict):
    season: str
    location: str
    flavor_notes: str

class FarmAgent:
    def __init__(self):
        graph_builder = StateGraph(State)
        graph_builder.add_node("FlavorNode", self.flavor_node)
        graph_builder.add_edge(START, "FlavorNode")
        graph_builder.add_edge("FlavorNode", END)
        self._agent = graph_builder.compile()

    async def flavor_node(self, state: State):
        season = state.get("season")
        location = state.get("location")

        if not season or not location:
            return {"error": "Missing 'season' or 'location' in input."}

        user_prompt = (
            f"The coffee farm is located in {location}, and the current season is {season.capitalize()}. "
            "Based on this information, what flavor profile can we expect from the coffee beans harvested here?\n\n"
            "Please describe expected flavor notes using coffee-tasting terminology (e.g. acidity, body, aroma, finish), "
            "and be concise but expressive (1–3 sentences max)."
        )

        system_prompt = "You are a coffee farm expert and flavor profile connoisseur."

        try:
            client = get_openai_client()
            if isinstance(client, AzureOpenAI):
                deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
                response = client.chat.completions.create(
                    model=deployment_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
            else:
                model = os.getenv("OPENAI_MODEL", "gpt-4o")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
            result = response.choices[0].message.content.strip()
        except Exception as e:
            result = f"LLM error: {e}"

        return {"flavor_notes": result}

    async def ainvoke(self, inputs: dict) -> dict:
        return await self._agent.ainvoke(inputs)
    
def get_openai_client():
    if os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
        print("[INFO] Using Azure OpenAI")
        return AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
    elif os.getenv("OPENAI_API_KEY"):
        print("[INFO] Using OpenAI")
        return OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
    else:
        raise EnvironmentError("No valid OpenAI or Azure OpenAI credentials found in environment.")