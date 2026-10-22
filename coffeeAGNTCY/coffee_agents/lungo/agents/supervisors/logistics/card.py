# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import AgentCapabilities, AgentCard, AgentSkill

# Logistics Supervisor Agent
LOGISTICS_SUPERVISOR_SKILL = AgentSkill(
    id="get_logistics_status",
    name="Get Logistics Status",
    description="Provides the current status and tracking of coffee shipments and logistics operations.",
    tags=["coffee", "logistics", "shipping"],
    examples=[
        "Where is my coffee shipment?",
        "What is the delivery status of order 123?",
        "Show me all shipments in transit.",
        "Has the Brazil farm shipment arrived at the port?",
    ],
)

LOGISTICS_SUPERVISOR_CARD = AgentCard(
    name="Logistics Supervisor agent",
    description="An AI agent that supervises and tracks coffee logistics and shipments.",
    version="1.0.0",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[LOGISTICS_SUPERVISOR_SKILL],
    # Caller identity only: this supervisor serves no A2A interface.
    supported_interfaces=[],
)
