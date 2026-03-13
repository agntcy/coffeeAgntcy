# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import (
    AgentCard,
    AgentInterface,
)
import os

PORT = int(os.getenv("PORT", "8881"))

# Define A2A agent card
AGENT_CARD = AgentCard(
    name="RecruiterAgent",
    description="An agent that helps find and recruit other agents based on specified criteria.",
    version="1.0.0",
    capabilities={"streaming": True},
    skills=[],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    supports_authenticated_extended_card=False,
    url=f"http://localhost:{PORT}",
    preferred_transport="JSONRPC",
    additional_interfaces=[
        AgentInterface(transport="jsonrpc", url=f"http://localhost:{PORT}"),
    ],
)