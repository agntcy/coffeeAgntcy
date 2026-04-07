# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill
)
from config.config import SLIM_SERVER, NATS_SERVER

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
    ]
)

AGENT_CARD = AgentCard(
    name='Colombia Coffee Farm',
    description='An AI agent that returns the yield of coffee beans in pounds for the Colombia farm.',
    version='1.0.0',
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False,
    preferred_transport="slimrpc",
    url=f"slim://{SLIM_SERVER}/lungo/agents/colombia_coffee_farm",
    additional_interfaces=[
        # point-to-point transport for direct client-agent communication
        AgentInterface(transport="slimrpc", url=f"slim://{SLIM_SERVER}/lungo/agents/colombia_coffee_farm"),
        # slim-based group comm and pub/sub transport
        AgentInterface(transport="slim", url=f"slim://{SLIM_SERVER}/lungo/agents/colombia_coffee_farm"),
        # nats-based pub/sub transport for broadcasting to multiple subscriber
        AgentInterface(transport="nats", url=f"nats://{NATS_SERVER}/lungo/agents/colombia_coffee_farm"),
        # jsonrpc endpoint for direct client-agent communication over http
        AgentInterface(transport="jsonrpc", url=f"http://0.0.0.0:{PORT}"),
    ],
)
