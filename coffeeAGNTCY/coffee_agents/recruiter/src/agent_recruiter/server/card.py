# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import AgentCard, AgentInterface, TransportProtocol


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
    preferred_transport=TransportProtocol.jsonrpc,
    url="http://0.0.0.0:8881",
    additional_interfaces=[
        # jsonrpc endpoint for direct client-agent communication over http
        AgentInterface(transport=TransportProtocol.jsonrpc, url="http://0.0.0.0:8881"),
    ],
)
