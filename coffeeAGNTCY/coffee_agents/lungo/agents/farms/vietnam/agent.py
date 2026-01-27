# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
Vietnam Farm Agent Module

This module implements a multi-agent system for the Vietnam coffee farm.
It uses ADK's automatic delegation pattern with sub_agents to route queries
to specialized sub-agents based on their descriptions:
- Inventory Agent: Handles yield and stock queries
- Orders Agent: Handles order placement and status queries
- General Agent: Fallback for unrecognized queries

The root agent automatically delegates to the appropriate sub-agent based on
the user's query and each sub-agent's description field.

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
# **LiteLLM**: Enables using various LLM providers with Google ADK.
# See: https://docs.litellm.ai/docs/tutorials/google_adk

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
# Each sub-agent has a specific role and a description that the root agent
# uses to determine when to delegate. The description field is crucial for
# ADK's automatic delegation mechanism.

inventory_agent = Agent(
    name="inventory_agent",
    model=LiteLlm(model=LLM_MODEL),
    description="Handles yield, stock, inventory, and product availability requests for the Vietnam coffee farm. Delegate to this agent for questions about coffee quantities, harvest estimates, or what's in stock.",
    instruction="""You are a helpful coffee farm cultivation manager in Vietnam who handles yield or inventory requests.
Return a random yield estimate for the coffee farm in Vietnam. Make sure the estimate is a reasonable value and in pounds.
Respond with ONLY the yield estimate number and unit (e.g., "45,000 pounds"). Do not add any other text or explanation.
If the user asked in lbs or pounds, respond with the estimate in pounds. If the user asked in kg or kilograms, convert the estimate to kg and respond with that value.""",
    tools=[],
)

orders_agent = Agent(
    name="orders_agent",
    model=LiteLlm(model=LLM_MODEL),
    description="Handles order-related queries for the Vietnam coffee farm including checking order status, placing new orders, and modifying existing orders. Delegate to this agent for any order or purchase related questions.",
    instruction="""You are an order assistant. Based on the user's question and the following order data, provide a concise and helpful response.
If they ask about a specific order number, provide its status.
If they ask about placing an order, generate a random order id and tracking number and format the response like:
Sure! Your order has been placed. Here are the details:

- **Order ID**: [random 5-digit number]
- **Tracking Number**: [random alphanumeric]

Let me know if you need anything else!

Order Data: {'12345': {'status': 'processing', 'estimated_delivery': '2 business days'}, '67890': {'status': 'shipped', 'tracking_number': 'ABCDEF123'}}""",
    tools=[],
)

general_agent = Agent(
    name="general_agent",
    model=LiteLlm(model=LLM_MODEL),
    description="Fallback agent for unclear, general, or off-topic queries that don't relate to inventory or orders. Delegate to this agent when the user's request doesn't fit inventory or order categories.",
    instruction='Respond with exactly this message and nothing else: "I\'m designed to help with inventory and order-related questions. Could you please rephrase your request?"',
    tools=[],
)

# ============================================================================
# Root Agent Definition (Agent Team Coordinator)
# ============================================================================
# The root agent uses ADK's automatic delegation pattern.
# It analyzes user queries and delegates to the appropriate sub-agent
# based on each sub-agent's description field.
# See: https://google.github.io/adk-docs/tutorials/agent-team/

root_agent = Agent(
    name="vietnam_farm_coordinator",
    model=LiteLlm(model=LLM_MODEL),
    description="The main coordinator agent for the Vietnam coffee farm. Routes requests to specialized sub-agents.",
    instruction="""You are the main coordinator for the Vietnam coffee farm, managing a team of specialized agents.
Your role is to analyze user queries and delegate to the appropriate specialist:

You have the following specialized sub-agents:
1. 'inventory_agent': Handles yield, stock, inventory, and product availability questions. Delegate to it for questions like "How much coffee do we have?", "What's the yield estimate?", "What's in stock?"
2. 'orders_agent': Handles order-related queries including status checks, placing orders, and modifications. Delegate to it for questions like "Place an order", "Check order status", "I want to buy coffee"
3. 'general_agent': Handles unclear or off-topic queries. Delegate to it when the request doesn't fit inventory or orders.

Analyze each user query carefully and delegate to the most appropriate sub-agent.
Do not try to answer questions directly - always delegate to the appropriate specialist.""",
    tools=[],
    sub_agents=[inventory_agent, orders_agent, general_agent],
)

# ============================================================================
# Session and Runner Configuration
# ============================================================================
# **Session**: Manages state for a user interaction.
# See: https://google.github.io/adk-docs/sessions/session/
#
# **Runner**: Orchestrates agent execution.
# See: https://google.github.io/adk-docs/runtime/event-loop/#runners-role-orchestrator

session_service = InMemorySessionService()

# Single runner for the root agent - ADK handles sub-agent delegation automatically
root_runner = Runner(
    agent=root_agent,
    app_name="vietnam_farm",
    session_service=session_service
)


# ============================================================================
# Agent Execution Functions
# ============================================================================


async def call_agent_async(query: str, runner: Runner, user_id: str, session_id: str) -> str:
    """Send a query to an agent runner and return the final response text."""
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


async def get_or_create_session(app_name: str, user_id: str, session_id: str):
    """Retrieve an existing session or create a new one if it doesn't exist."""
    session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if session is None:
        session = await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    return session


async def run_vietnam_agent(query: str) -> str:
    """Execute the Vietnam Farm Agent workflow.

    Workflow:
        1. Root agent receives the query
        2. Root agent automatically delegates to appropriate sub-agent based on descriptions
        3. Sub-agent processes query and returns response
    """
    # Static user_id is intentional: ADK sessions require a user context,
    # and a shared context is sufficient for this agent's use case.
    user_id = "user_1"
    session_id = "main_session"

    # Initialize session for the root agent
    await get_or_create_session(app_name="vietnam_farm", user_id=user_id, session_id=session_id)

    logger.info(f"User Query: {query}")

    # Execute query with root agent - delegation happens automatically
    response = await call_agent_async(query, root_runner, user_id, session_id)

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
# Run this file directly to test the agent with sample queries.


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
