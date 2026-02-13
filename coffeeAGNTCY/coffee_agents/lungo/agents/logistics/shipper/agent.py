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

logger = logging.getLogger("lungo.shipper_agent.agent")

LITELLM_PROXY_BASE_URL = os.getenv("LITELLM_PROXY_BASE_URL")
LITELLM_PROXY_API_KEY = os.getenv("LITELLM_PROXY_API_KEY")

if LITELLM_PROXY_API_KEY and LITELLM_PROXY_BASE_URL:
    os.environ["LITELLM_PROXY_API_KEY"] = LITELLM_PROXY_API_KEY
    os.environ["LITELLM_PROXY_API_BASE"] = LITELLM_PROXY_BASE_URL
    logger.info(f"Using LiteLLM Proxy: {LITELLM_PROXY_BASE_URL}")
    litellm.use_litellm_proxy = True
else:
    logger.info("Using direct LLM instance")

shipper_agent_adk = Agent(
    name="shipper_agent",
    model=LiteLlm(model=LLM_MODEL),
    description="Handles shipping and delivery for coffee orders in the logistics workflow.",
    instruction="""You are the Shipper agent in a logistics workflow.

Your responsibilities:
1. Receive messages in format: "STATUS | Sender -> Receiver: Details"
2. Handle two transitions:
   - HANDOVER_TO_SHIPPER -> CUSTOMS_CLEARANCE
   - PAYMENT_COMPLETE -> DELIVERED

When you receive HANDOVER_TO_SHIPPER:
- Respond: "CUSTOMS_CLEARANCE | Shipper -> Accountant: Customs docs validated and cleared"

When you receive PAYMENT_COMPLETE:
- Respond: "DELIVERED | Shipper -> Supervisor: Final handoff completed"

For any other status:
- Respond: "Shipper remains IDLE. No further action required."

CRITICAL: Follow the exact format. Do not add extra text.""",
    tools=[],
)

session_service = InMemorySessionService()

shipper_runner = Runner(
    agent=shipper_agent_adk,
    app_name="shipper_agent",
    session_service=session_service
)

async def get_or_create_session(app_name: str, user_id: str, session_id: str):
    session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if session is None:
        session = await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    return session

def process_shipper_logic(raw_message: str) -> str:
    """Process shipper business logic."""
    status = extract_status(raw_message)
    order_id = ensure_order_id(raw_message)

    if status is LogisticsStatus.HANDOVER_TO_SHIPPER:
        next_status = LogisticsStatus.CUSTOMS_CLEARANCE
        msg = build_transition_message(
            order_id=order_id,
            sender="Shipper",
            receiver="Accountant",
            to_state=next_status.value,
            details="Customs docs validated and cleared",
        )
        return msg

    if status is LogisticsStatus.PAYMENT_COMPLETE:
        next_status = LogisticsStatus.DELIVERED
        msg = build_transition_message(
            order_id=order_id,
            sender="Shipper",
            receiver="Supervisor",
            to_state=next_status.value,
            details="Final handoff completed",
        )
        return msg

    return "Shipper remains IDLE. No further action required."

@agent(name="shipper_agent")
class ShipperAgent:
    def __init__(self):
        """Initialize the ShipperAgent using Google ADK."""
        self.runner = shipper_runner
        self.app_name = "shipper_agent"

    async def ainvoke(self, user_message: str) -> str:
        """
        Process a message through the shipper agent.
        
        Args:
            user_message (str): The incoming message from the logistics system.
            
        Returns:
            str: The response from the shipper agent.
        """
        user_id = "user_1"
        session_id = "main_session"

        await get_or_create_session(app_name=self.app_name, user_id=user_id, session_id=session_id)

        logger.info(f"Shipper received: {user_message}")
        response = process_shipper_logic(user_message)
        logger.info(f"Shipper response: {response}")
        
        return response