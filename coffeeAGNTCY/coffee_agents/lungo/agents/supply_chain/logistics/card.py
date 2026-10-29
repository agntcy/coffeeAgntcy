# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from agntcy_app_sdk.semantic.a2a.transport_types import InterfaceTransport

from config.config import SLIM_SERVER

AGENT_ID = "supply-chain-logistics-agent"

AGENT_SKILL = AgentSkill(
    id="confirm_transport",
    name="Confirm Transport",
    description=(
        "States this carrier's transport options, transit times, costs and "
        "capacity, and confirms or declines a transport plan."
    ),
    tags=["coffee", "logistics", "transport", "negotiation"],
    examples=[
        "Which transport options do you have to Warehouse W?",
        "Can you confirm expedited capacity for this lot?",
        "Do you confirm this plan?",
    ],
)

AGENT_CARD = AgentCard(
    name="Logistics agent",
    description=(
        "A carrier that confirms transport options, capacity and cost for a "
        "supply commitment negotiation."
    ),
    version="1.0.0",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supported_interfaces=[
        AgentInterface(
            protocol_binding=InterfaceTransport.SLIM_PATTERNS,
            url=f"slim://{SLIM_SERVER}/lungo/agents/{AGENT_ID}",
        ),
    ],
)
