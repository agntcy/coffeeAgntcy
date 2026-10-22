# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os

import config.config
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from agntcy_app_sdk.semantic.a2a.transport_types import InterfaceTransport

PORT = os.getenv("FARM_AGENT_PORT", "9998")
AGENT_ID = "colombia_coffee_farm"

AGENT_SKILL = AgentSkill(
    id="get_yield",
    name="Get Coffee Yield",
    description="Returns the coffee farm's yield in lb.",
    tags=["coffee", "farm"],
    examples=[
        "What is the yield of the Colombia coffee farm?",
        "How much coffee does the Colombia farm produce?",
        "What is the yield of the Colombia coffee farm in pounds?",
        "How many pounds of coffee does the Colombia farm produce?",
    ],
)

AGENT_CARD = AgentCard(
    name="Colombia Coffee Farm",
    description="An AI agent that returns the yield of coffee beans in pounds for the Colombia farm.",
    version="1.0.0",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    # Ordered by preference: clients negotiate in this order.
    supported_interfaces=[
        # slim-based group messaging and pub/sub transport
        AgentInterface(
            protocol_binding=InterfaceTransport.SLIM_PATTERNS,
            url=f"slim://{config.config.SLIM_SERVER}/lungo/agents/{AGENT_ID}",
        ),
        # nats-based pub/sub transport for broadcasting to multiple subscriber
        AgentInterface(
            protocol_binding=InterfaceTransport.NATS_PATTERNS,
            url=f"nats://{config.config.NATS_SERVER}/lungo/agents/{AGENT_ID}",
        ),
        # jsonrpc endpoint for direct client-agent communication over http
        AgentInterface(
            protocol_binding=InterfaceTransport.JSONRPC,
            url=f"http://0.0.0.0:{PORT}",
        ),
    ],
)
