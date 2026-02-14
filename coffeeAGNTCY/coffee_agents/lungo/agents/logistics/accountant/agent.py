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

from ioa_observe.sdk.decorators import agent, graph

from common.logistics_states import (
    LogisticsStatus,
    extract_status,
    build_transition_message,
    ensure_order_id,
)

logger = logging.getLogger("lungo.accountant_agent.agent")

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


accountant_agent = Agent(
    name="accountant_agent",
    model=LiteLlm(model=LLM_MODEL),
    description="Handles payment processing for coffee orders in the logistics workflow.",
    instruction="""You are the Accountant agent in a logistics workflow.

Your responsibilities:
1. Receive messages from the logistics system in format: "STATUS | Sender -> Receiver: Details"
2. Extract the order status and order_id from the message
3. Process payment verification when status is CUSTOMS_CLEARANCE
4. Transition to PAYMENT_COMPLETE after verifying payment
5. Remain idle for other statuses

When you receive CUSTOMS_CLEARANCE status:
- Extract the order_id from the message
- Respond EXACTLY in this format: "PAYMENT_COMPLETE | Accountant -> Shipper: Payment verified and captured"

For any other status:
- Respond EXACTLY: "Accountant remains IDLE. No further action required."

CRITICAL: Follow the exact format. Do not add extra text or explanations.""",
    tools=[],
)

# ============================================================================
# Session and Runner Configuration
# ============================================================================
session_service = InMemorySessionService()

accountant_runner = Runner(
    agent=accountant_agent,
    app_name="accountant_agent",
    session_service=session_service
)

async def get_or_create_session(app_name: str, user_id: str, session_id: str):
    """Retrieve an existing session or create a new one if it doesn't exist."""
    session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if session is None:
        session = await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    return session

def process_accountant_logic(raw_message: str) -> str:
    """Process accountant business logic."""
    status = extract_status(raw_message)
    order_id = ensure_order_id(raw_message)

    if status is LogisticsStatus.CUSTOMS_CLEARANCE:
        next_status = LogisticsStatus.PAYMENT_COMPLETE
        msg = build_transition_message(
            order_id=order_id,
            sender="Accountant",
            receiver="Shipper",
            to_state=next_status.value,
            details="Payment verified and captured",
        )
        return msg

    return "Accountant remains IDLE. No further action required."


@agent(name="accountant_agent")
class AccountantAgent:
    def __init__(self):
        """Initialize the AccountantAgent using Google ADK."""
        self.runner = accountant_runner
        self.app_name = "accountant_agent"

    async def ainvoke(self, user_message: str) -> str:
        """
        Process a message through the accountant agent.
        
        Args:
            user_message (str): The incoming message from the logistics system.
            
        Returns:
            str: The response from the accountant agent.
        """

        user_id = "user_1"
        session_id = "main_session"
        
        await get_or_create_session(app_name=self.app_name, user_id=user_id, session_id=session_id)

        logger.info(f"Accountant received: {user_message}")
        response = process_accountant_logic(user_message)
        logger.info(f"Accountant response: {response}")

        return response