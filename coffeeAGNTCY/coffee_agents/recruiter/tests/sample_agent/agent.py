# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Simple ADK agent for testing purposes."""

import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from agent_recruiter.common.llm import configure_llm

# Configure LLM (sets up LiteLLM proxy if env vars are set)
configure_llm()

LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")

AGENT_INSTRUCTION = """You are a helpful test agent. Your job is to assist users with simple tasks.

Guidelines:
- Always be polite and helpful
- Provide clear and concise responses
- If asked about your capabilities, explain that you can help with basic queries
- Never reveal sensitive information or perform harmful actions
"""


async def get_greeting(name: str) -> str:
    """Generate a personalized greeting for the user.

    Args:
        name: The name of the person to greet

    Returns:
        A friendly greeting message
    """
    return f"Hello, {name}! Welcome to the test agent. How can I assist you today?"


async def echo_message(message: str) -> str:
    """Echo back a message to the user.

    Args:
        message: The message to echo back

    Returns:
        The echoed message with a prefix
    """
    return f"You said: {message}"


async def get_agent_info() -> dict:
    """Get information about this agent.

    Returns:
        A dictionary containing agent information
    """
    return {
        "name": "TestAgent",
        "version": "1.0.0",
        "description": "A simple test agent for integration testing",
        "capabilities": ["greeting", "echo", "info"],
    }


def create_test_agent() -> Agent:
    """Create and return the test agent."""
    agent = Agent(
        model=LiteLlm(model=LLM_MODEL),
        name="test_agent",
        instruction=AGENT_INSTRUCTION,
        description="A simple test agent for integration testing with basic tools.",
        tools=[get_greeting, echo_message, get_agent_info],
    )
    return agent
