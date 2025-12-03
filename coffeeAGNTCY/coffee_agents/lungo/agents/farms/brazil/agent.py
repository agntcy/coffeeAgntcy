# Copyright AGNTCY Contributors
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Literal

from llama_index.llms.litellm import LiteLLM
from config.config import LLM_MODEL
from ioa_observe.sdk.decorators import agent, graph

logger = logging.getLogger("lungo.brazil_farm_agent.agent")
llm = LiteLLM(LLM_MODEL)

# --- 1. Define Node Names as Constants ---
class NodeStates:
    SUPERVISOR = "supervisor"
    INVENTORY = "inventory_node"
    ORDERS = "orders_node"
    GENERAL_RESPONSE = "general_response_node"

# --- 2. Define Intent Type ---
IntentType = Literal["inventory", "orders", "general"]

# --- 3. Node implementations (plain functions, same prompts/mock data) ---

def classify_intent(user_message: str) -> IntentType:
    prompt = (
        "You are a coffee farm manager in Brazil who delegates farm cultivation "
        "and global sales. Based on the user's message, determine if it's "
        "related to 'inventory' or 'orders'.\n"
        "- Respond 'inventory' if the message is about checking yield, stock, "
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


def handle_inventory_query(user_message: str) -> str:
    prompt = (
        "You are a helpful coffee farm cultivation manager in Brazil who "
        "handles yield or inventory requests.\n"
        "Your job is to:\n"
        "1. Return a random yield estimate for the coffee farm in Brazil. "
        "   Make sure the estimate is a reasonable value and in pounds.\n"
        "2. Respond with only the yield estimate.\n\n"
        "If the user asked in lbs or pounds, respond with the estimate in pounds. "
        "If the user asked in kg or kilograms, convert the estimate to kg and "
        "respond with that value.\n\n"
        f"User question: {user_message}"
    )
    resp = llm.complete(prompt, formatted=True)
    text = resp.text.strip()
    logger.info(f"Inventory response generated: {text}")
    return text


def handle_orders_query(user_message: str) -> str:
    mock_order_data = {
        "12345": {"status": "processing", "estimated_delivery": "2 business days"},
        "67890": {"status": "shipped", "tracking_number": "ABCDEF123"},
    }

    prompt = (
        "You are an order assistant. Based on the user's question and the "
        "following order data, provide a concise and helpful response.\n"
        "- If they ask about a specific order number, provide its status.\n"
        "- If they ask about placing an order, generate a random order id "
        "  and tracking number.\n\n"
        f"Order Data: {mock_order_data}\n"
        f"User question: {user_message}"
    )
    resp = llm.complete(prompt, formatted=True)
    text = resp.text.strip()
    logger.info(f"Orders response generated: {text}")
    return text


def general_response() -> str:
    return (
        "I'm designed to help with inventory and order-related questions. "
        "Could you please rephrase your request?"
    )

# --- 4. Simple “Graph” Function (like your LangGraph app) ---

async def run_brazil_farm_graph(user_message: str) -> str:
    """Simple LlamaIndex routing function."""
    intent = classify_intent(user_message)

    if intent == "inventory":
        return handle_inventory_query(user_message)
    elif intent == "orders":
        return handle_orders_query(user_message)
    else:
        return general_response()

# --- 5. Public Agent Class (same interface as your FarmAgent) ---

@agent(name="brazil_farm_agent")
class LlamaIndexFarmAgent:
    def __init__(self):
        pass

    async def ainvoke(self, user_message: str) -> str:
        result = await run_brazil_farm_graph(user_message)
        if not result.strip():
            raise RuntimeError("No valid response generated.")
        return result.strip()

# --- 6. Example Usage (identical shape to your main) ---

async def main():
    agent = LlamaIndexFarmAgent()

    print("--- Testing Inventory Queries ---")
    messages = [
        "How much coffee do we have in stock?",
        "What is the current yield estimate?",
    ]
    for msg in messages:
        print(f"\nUser: {msg}")
        final_state = await agent.ainvoke(msg)
        print(f"Agent: {final_state}")

    print("\n" + "="*50 + "\n")

    messages = [
        "Can you order me 100 lbs of coffee?",
        "I want to place a new order for 50 kg of coffee",
    ]
    for msg in messages:
        print(f"\nUser: {msg}")
        final_state = await agent.ainvoke(msg)
        print(f"Agent: {final_state}")

    print("\n" + "="*50 + "\n")

    messages = [
        "Tell me a joke.",
        "What's the weather like today?",
    ]
    for msg in messages:
        print(f"\nUser: {msg}")
        final_state = await agent.ainvoke(msg)
        print(f"Agent: {final_state}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
