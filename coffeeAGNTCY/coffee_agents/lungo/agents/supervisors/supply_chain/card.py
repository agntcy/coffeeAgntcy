# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import AgentCapabilities, AgentCard, AgentSkill

# Buyer agent: the supervisor of the Supply Chain Commitment workflow.
BUYER_SKILL = AgentSkill(
    id="negotiate_supply_commitment",
    name="Negotiate Supply Commitment",
    description=(
        "Moderates a negotiation between a buyer, three suppliers and a "
        "logistics provider, and records whether a commitment was made."
    ),
    tags=["coffee", "supply chain", "negotiation"],
    examples=[
        "Run the explicit case with the baseline configuration.",
        "Run the infeasible case with L9.",
    ],
)

BUYER_CARD = AgentCard(
    name="Buyer agent",
    description=(
        "A procurement agent that negotiates a coffee supply commitment with "
        "three suppliers and a logistics provider."
    ),
    version="1.0.0",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[BUYER_SKILL],
    # Caller identity only: the Buyer serves no A2A interface. It reaches the
    # other agents through SLIM group sessions.
    supported_interfaces=[],
)
