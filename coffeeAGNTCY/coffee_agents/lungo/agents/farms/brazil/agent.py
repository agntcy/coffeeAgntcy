# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Literal

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.litellm import LiteLLM
from config.config import LLM_MODEL
from ioa_observe.sdk.decorators import tool, agent, graph
from llama_index.llms.azure_openai import AzureOpenAI
import os

logger = logging.getLogger("lungo.brazil_farm_agent.agent")
# Brazil farm agent is a llama_index based agent
# Initialize llm with llama_index_LiteLLM
litellm_proxy_base_url = os.getenv("LITELLM_PROXY_BASE_URL")
litellm_proxy_api_key = os.getenv("LITELLM_PROXY_API_KEY")

if litellm_proxy_base_url and litellm_proxy_api_key:
    logger.info(f"Using LLM via LiteLLM proxy: {litellm_proxy_base_url}")
    llm = AzureOpenAI(
        engine=LLM_MODEL,
        azure_endpoint=litellm_proxy_base_url,
        api_key=litellm_proxy_api_key
    )
else:
    llm = LiteLLM(LLM_MODEL)

# --- 1. Define Intent Type ---
IntentType = Literal["inventory", "orders", "general"]

# --- 2. Tool Functions ---

@tool(name="inventory_tool")
def handle_inventory_tool(user_message: str) -> str:
    """Handle inventory-related queries and provide yield estimates."""
    prompt = (
        "You are a helpful coffee farm cultivation manager in Brazil who handles yield or inventory requests. "
        "Your job is to return a random yield estimate for the coffee farm in Brazil. "
        "Make sure the estimate is a reasonable value and in pounds. "
        "Respond with only the yield estimate. "
        "If the user asked in lbs or pounds, respond with the estimate in pounds. "
        "If the user asked in kg or kilograms, convert the estimate to kg and respond with that value.\n\n"
        "User question: {user_message}"
    ).format(user_message=user_message)
    resp = llm.complete(prompt, formatted=True)
    text = resp.text.strip()
    logger.info(f"Inventory response generated: {text}")
    return text


@tool(name="orders_tool")
def handle_orders_tool(user_message: str) -> str:
    """Handle order-related queries including placing orders and checking status."""
    mock_order_data = {
        "12345": {"status": "processing", "estimated_delivery": "2 business days"},
        "67890": {"status": "shipped", "tracking_number": "ABCDEF123"},
    }

    prompt = (
        "You are an order assistant. Based on the user's question and the "
        "following order data, provide a concise and helpful response.\n"
        "- If they ask about a specific order number, provide its status.\n"
        "- If they ask about placing an order, generate a new random order id "
        "  and tracking number.\n\n"
        f"Order Data: {mock_order_data}\n"
        f"User question: {user_message}"
    )
    resp = llm.complete(prompt, formatted=True)
    text = resp.text.strip()
    logger.info(f"Orders response generated: {text}")
    return text

# --- 3. Intent Classification ---

def classify_intent(user_message: str) -> IntentType:
    prompt = (
        "You are a coffee farm manager in Brazil who delegates farm cultivation "
        "and global sales. Based on the user's message, determine if it's "
        "related to 'inventory' or 'orders'.\n"
        "- Respond 'inventory' if the message is about checking yield, stock,inventory, "
        "  product availability, or specific coffee item details.\n"
        "- Respond 'orders' if the message is about checking order status, "
        "  placing an order, or modifying an existing order.\n"
        "- If unsure, respond 'general'.\n\n"
        f"User message: {user_message}"
    )
    resp = llm.complete(prompt, formatted=True)
    intent_raw = resp.text.strip().lower()
    logger.info(f"Supervisor intent raw: {intent_raw}")

    # Be tolerant of extra text: look for keyword presence.
    if "inventory" in intent_raw:
        return "inventory"
    if "orders" in intent_raw or "order" in intent_raw:
        return "orders"
    return "general"

# --- 4. Routing Function ---

# Routes to appropriate FunctionAgent based on intent classification

async def run_brazil_farm_routing(user_message: str) -> str:
    """Route to appropriate FunctionAgent based on intent with lazy initialization."""
    intent = classify_intent(user_message)
    if intent == "inventory":
        inventory_agent = FunctionAgent(
            tools=[handle_inventory_tool],
            llm=llm,
            system_prompt="Return only the exact output from the tool. Do not add any additional text or explanation."
        )
        response = await inventory_agent.run(user_message)
        return str(response)
    elif intent == "orders":
        orders_agent = FunctionAgent(
            tools=[handle_orders_tool],
            llm=llm,
            system_prompt="Return only the exact output from the tool. Do not add any additional text or explanation."
        )
        response = await orders_agent.run(user_message)
        return str(response)
    else:
        return (
            "I'm designed to help with inventory and order-related questions. "
            "Could you please rephrase your request?"
        )

# --- 5. Public Agent Class ---

# Main agent interface that handles intent classification and routing
# LlamaIndex agent workflow examples: https://developers.llamaindex.ai/python/examples/agent/agent_workflow_basic/

@agent(name="brazil_farm_agent")
class FarmAgent:
    def __init__(self):
        pass

    async def llama_index_invoke(self, user_message: str) -> str:
        result = await run_brazil_farm_routing(user_message)
        if not result.strip():
            raise RuntimeError("No valid response generated.")
        return result.strip()

# --- 6. Example Usage ---

async def main():
    agent = FarmAgent()

    print("--- Testing Inventory Queries ---")
    messages = [
        "How much coffee do we have in stock?",
        "What is the current yield estimate?",
    ]
    for msg in messages:
        print(f"\nUser: {msg}")
        final_state = await agent.llama_index_invoke(msg)
        print(f"Agent: {final_state}")

    print("\n" + "="*50 + "\n")

    messages = [
        "Can you order me 100 lbs of coffee?",
        "I want to place a new order for 50 kg of coffee",
    ]
    for msg in messages:
        print(f"\nUser: {msg}")
        final_state = await agent.llama_index_invoke(msg)
        print(f"Agent: {final_state}")

    print("\n" + "="*50 + "\n")

    messages = [
        "Tell me a joke.",
        "What's the weather like today?",
    ]
    for msg in messages:
        print(f"\nUser: {msg}")
        final_state = await agent.llama_index_invoke(msg)
        print(f"Agent: {final_state}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
