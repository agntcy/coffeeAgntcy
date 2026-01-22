# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Vietnam Farm Agent Module

This module implements a multi-agent system for the Vietnam coffee farm.
It uses intent-based routing to delegate queries to specialized sub-agents:
- Inventory Agent: Handles yield and stock queries
- Orders Agent: Handles order placement and status queries
- General Agent: Fallback for unrecognized queries

The system uses Google ADK with LiteLLM for LLM interactions.
"""

import logging

import os
import asyncio
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import litellm
from config.config import LLM_MODEL
from ioa_observe.sdk.decorators import agent

logger = logging.getLogger("lungo.vietnam_farm_agent.agent")

# ============================================================================
# LLM Configuration
# ============================================================================
LITELLM_PROXY_BASE_URL = os.getenv("LITELLM_PROXY_BASE_URL")
LITELLM_PROXY_API_KEY = os.getenv("LITELLM_PROXY_API_KEY")

# Configure LiteLLM proxy if environment variables are set
if LITELLM_PROXY_API_KEY and LITELLM_PROXY_BASE_URL:
    os.environ["LITELLM_PROXY_API_KEY"] = LITELLM_PROXY_API_KEY
    os.environ["LITELLM_PROXY_API_BASE"] = LITELLM_PROXY_BASE_URL
    logger.info(f"Using LiteLLM Proxy: {LITELLM_PROXY_BASE_URL}")
    litellm.use_litellm_proxy = True
else:
    logger.info("Using direct LLM instance")

# ============================================================================
# Sub-Agent Definitions
# ============================================================================

inventory_agent = Agent(
    name="inventory_agent",
    model=LiteLlm(model=LLM_MODEL),
    description="Handles yield and inventory requests for the Vietnam coffee farm.",
    instruction="""You are a helpful coffee farm cultivation manager in Vietnam who handles yield or inventory requests. 
Your job is to:
1. Return a random yield estimate for the coffee farm in Vietnam. Make sure the estimate is a reasonable value and in pounds.
2. Respond with only the yield estimate.

If the user asked in lbs or pounds, respond with the estimate in pounds. If the user asked in kg or kilograms, convert the estimate to kg and respond with that value.""",
    tools=[],
)

orders_agent = Agent(
    name="orders_agent",
    model=LiteLlm(model=LLM_MODEL),
    description="Handles order-related queries for the Vietnam coffee farm.",
    instruction="""You are an order assistant. Based on the user's question and the following order data, provide a concise and helpful response.
If they ask about a specific order number, provide its status. 
If they ask about placing an order, generate a random order id and tracking number.

Order Data: {'12345': {'status': 'processing', 'estimated_delivery': '2 business days'}, '67890': {'status': 'shipped', 'tracking_number': 'ABCDEF123'}}""",
    tools=[],
)

general_agent = Agent(
    name="general_agent",
    model=LiteLlm(model=LLM_MODEL),
    description="Fallback agent for unclear or general queries.",
    instruction="""Respond with exactly this message: "I'm designed to help with inventory and order-related questions. Could you please rephrase your request?" """,
    tools=[],
)

intent_classifier = Agent(
    name="intent_classifier",
    model=LiteLlm(model=LLM_MODEL),
    description="Classifies user intent to route to appropriate agent.",
    instruction="""You are a coffee farm manager in Vietnam who delegates farm cultivation and global sales. Based on the user's message, determine if it's related to 'inventory' or 'orders'.

Respond with 'inventory' if the message is about checking yield, stock, product availability, or specific coffee item details.
Respond with 'orders' if the message is about checking order status, placing an order, or modifying an existing order.
If unsure, respond with 'general'.

Return ONLY ONE WORD: inventory, orders, or general. Nothing else.""",
    tools=[],
)

# ============================================================================
# Session and Runner Configuration
# ============================================================================

session_service = InMemorySessionService()
intent_runner = Runner(
    agent=intent_classifier,
    app_name="vietnam_farm",
    session_service=session_service
)

inventory_runner = Runner(
    agent=inventory_agent,
    app_name="vietnam_farm",
    session_service=session_service
)

orders_runner = Runner(
    agent=orders_agent,
    app_name="vietnam_farm",
    session_service=session_service
)

general_runner = Runner(
    agent=general_agent,
    app_name="vietnam_farm",
    session_service=session_service
)


# ============================================================================
# Agent Execution Functions
# ============================================================================


async def call_agent_async(query: str, runner, user_id: str, session_id: str) -> str:
    """Sends a query to an agent and returns the final response."""
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response."

    async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            break

    return final_response_text


async def detect_intent(message: str, user_id: str, session_id: str) -> str:
    """Classify user intent using the intent classifier agent.

    Returns one of: 'inventory', 'orders', or 'general'.
    """
    result = await call_agent_async(message, intent_runner, user_id, session_id)
    intent = result.strip().lower()

    if "inventory" in intent:
        return "inventory"
    elif "order" in intent:
        return "orders"
    else:
        return "general"


def get_runner_for_intent(intent: str):
    """Map intent to the corresponding agent runner.

    Returns a tuple of (runner, agent_name) for the matched intent.
    """
    if intent == "inventory":
        return inventory_runner, "Inventory Agent"
    elif intent == "orders":
        return orders_runner, "Orders Agent"
    else:
        return general_runner, "General Agent"


async def get_or_create_session(app_name: str, user_id: str, session_id: str):
    """Retrieve an existing session or create a new one.

    This prevents AlreadyExistsError on repeated agent invocations.
    """
    session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if session is None:
        session = await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    return session


async def run_vietnam_agent(query: str) -> str:
    """Execute the Vietnam Farm Agent workflow.

    Workflow:
        1. Classify user intent
        2. Route to appropriate sub-agent
        3. Execute query and return response
    """
    user_id = "user_1"

    # Initialize sessions for all agents
    await get_or_create_session(app_name="vietnam_farm", user_id=user_id, session_id="intent_session")
    await get_or_create_session(app_name="vietnam_farm", user_id=user_id, session_id="inventory_session")
    await get_or_create_session(app_name="vietnam_farm", user_id=user_id, session_id="orders_session")
    await get_or_create_session(app_name="vietnam_farm", user_id=user_id, session_id="general_session")

    logger.info(f"User Query: {query}")

    # Classify intent and route to appropriate agent
    intent = await detect_intent(query, user_id, "intent_session")
    logger.info(f"[Supervisor] Intent determined: {intent}")

    runner, agent_name = get_runner_for_intent(intent)
    logger.info(f"[Router] Routing to: {agent_name}")

    session_map = {
        "inventory": "inventory_session",
        "orders": "orders_session",
        "general": "general_session"
    }
    session_id = session_map.get(intent, "general_session")

    # Execute query with selected agent
    response = await call_agent_async(query, runner, user_id, session_id)

    logger.info(f"Agent Response: {response}")
    return response


# ============================================================================
# Public Agent Interface
# ============================================================================


@agent(name="vietnam_farm_agent")
class FarmAgent:
    """Vietnam Farm Agent with IOA observability integration."""

    def __init__(self):
        pass

    async def google_adk_agent_invoke(self, user_message: str) -> str:
        """Process a user message and return the agent response."""
        result = await run_vietnam_agent(user_message)
        if not result.strip():
            raise RuntimeError("No valid response generated.")
        return result.strip()


# ============================================================================
# Development Testing
# ============================================================================


async def main():
    """Run example queries against the Vietnam Farm Agent."""
    agent = FarmAgent()

    print("--- Testing Inventory Queries ---")
    messages = [
        "How much coffee do we have in stock?",
        "What is the current yield estimate?",
    ]
    for msg in messages:
        print(f"\nUser: {msg}")
        final_state = await agent.google_adk_agent_invoke(msg)
        print(f"Agent: {final_state}")

    print("\n" + "=" * 50 + "\n")

    messages = [
        "Can you order me 100 lbs of coffee?",
        "I want to place a new order for 50 kg of coffee",
    ]
    for msg in messages:
        print(f"\nUser: {msg}")
        final_state = await agent.google_adk_agent_invoke(msg)
        print(f"Agent: {final_state}")

    print("\n" + "=" * 50 + "\n")

    messages = [
        "Tell me a joke.",
        "What's the weather like today?",
    ]
    for msg in messages:
        print(f"\nUser: {msg}")
        final_state = await agent.google_adk_agent_invoke(msg)
        print(f"Agent: {final_state}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
