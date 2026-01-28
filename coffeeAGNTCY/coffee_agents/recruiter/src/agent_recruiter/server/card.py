# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import AgentCard


# Define A2A agent card
AGENT_CARD = AgentCard(
    name="RecruiterAgent",
    url="http://localhost:8881",
    description="An agent that helps find and recruit other agents based on specified criteria.",
    version="1.0.0",
    capabilities={"streaming": True},
    skills=[],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    supports_authenticated_extended_card=False,
)