# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from agntcy_app_sdk.semantic.a2a.transport_types import InterfaceTransport
from config.config import SLIM_SERVER

AGENT_ID = "logistics_helpdesk_agent"

AGENT_SKILL = AgentSkill(
    id="helpdesk_support",
    name="Helpdesk Support",
    description="Provides assistance with logistics and support queries.",
    tags=["logistics", "support", "helpdesk"],
    examples=[
        "How can I track my shipment?",
        "What is the status of my order?",
        "Can you help me with a logistics issue?",
        "I need assistance with my delivery.",
    ],
)

AGENT_CARD = AgentCard(
    name="Logistics Helpdesk",
    description="An AI agent that provides logistics and support assistance for helpdesk queries.",
    version="1.0.0",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supported_interfaces=[
        # slim-based group messaging transport
        AgentInterface(
            protocol_binding=InterfaceTransport.SLIM_PATTERNS,
            url=f"slim://{SLIM_SERVER}/lungo/agents/{AGENT_ID}",
        ),
    ],
)
