# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import litellm
from config.config import LLM_MODEL

from ioa_observe.sdk.decorators import agent

from common.logistics_states import (
    LogisticsStatus,
    extract_status,
    build_transition_message,
    ensure_order_id,
)

logger = logging.getLogger("lungo.farm_agent.agent")

# Configure LiteLLM proxy if environment variables are set
LITELLM_PROXY_BASE_URL = os.getenv("LITELLM_PROXY_BASE_URL")
LITELLM_PROXY_API_KEY = os.getenv("LITELLM_PROXY_API_KEY")

if LITELLM_PROXY_API_KEY and LITELLM_PROXY_BASE_URL:
    os.environ["LITELLM_PROXY_API_KEY"] = LITELLM_PROXY_API_KEY
    os.environ["LITELLM_PROXY_API_BASE"] = LITELLM_PROXY_BASE_URL
    logger.info(f"Using LiteLLM Proxy: {LITELLM_PROXY_BASE_URL}")
    litellm.use_litellm_proxy = True
else:
    logger.info("Using direct LLM instance")


farm_agent_adk = Agent(
    name="farm_agent",
    model=LiteLlm(model=LLM_MODEL),
    description="Handles order processing for Tatooine Farm in the logistics workflow.",
    instruction="""You are the Tatooine Farm agent in a logistics workflow.

Your responsibilities:
1. Receive messages in format: "STATUS | Sender -> Receiver: Details"
2. Handle order reception and prepare shipments
3. Transition from RECEIVED_ORDER to HANDOVER_TO_SHIPPER

When you receive RECEIVED_ORDER:
- Respond: "HANDOVER_TO_SHIPPER | Tatooine Farm -> Shipper: Prepared shipment and documentation"

For any other status:
- Respond: "Logistic Farm remains IDLE. No further action required."

CRITICAL: Follow the exact format. Do not add extra text.""",
    tools=[],
)

session_service = InMemorySessionService()

farm_runner = Runner(
    agent=farm_agent_adk,
    app_name="farm_agent",
    session_service=session_service
)

async def get_or_create_session(app_name: str, user_id: str, session_id: str):
    session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if session is None:
        session = await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    return session

def process_farm_logic(raw_message: str) -> str:
    """Process farm business logic."""
    status = extract_status(raw_message)
    order_id = ensure_order_id(raw_message)

    if status is LogisticsStatus.RECEIVED_ORDER:
        next_status = LogisticsStatus.HANDOVER_TO_SHIPPER
        msg = build_transition_message(
            order_id=order_id,
            sender="Tatooine Farm",
            receiver="Shipper",
            to_state=next_status.value,
            details="Prepared shipment and documentation",
        )
        return msg

    return "Logistic Farm remains IDLE. No further action required."

@agent(name="farm_agent")
class FarmAgent:
    def __init__(self):
        """Initialize the FarmAgent using Google ADK."""
        self.runner = farm_runner
        self.app_name = "farm_agent"

    async def ainvoke(self, user_message: str) -> str:
        """
        Process a message through the farm agent.
        
        Args:
            user_message (str): The incoming message from the logistics system.
            
        Returns:
            str: The response from the farm agent.
        """
        user_id = "user_1"
        session_id = "main_session"

        await get_or_create_session(app_name=self.app_name, user_id=user_id, session_id=session_id)

        logger.info(f"Farm received: {user_message}")
        response = process_farm_logic(user_message)
        logger.info(f"Farm response: {response}")

        return response