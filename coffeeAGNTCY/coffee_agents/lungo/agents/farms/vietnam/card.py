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

PORT = os.getenv("FARM_AGENT_PORT", "9997")
AGENT_ID = "vietnam_coffee_farm"

AGENT_SKILL = AgentSkill(
    id="get_yield",
    name="Get Coffee Yield",
    description="Returns the coffee farm's yield in lb.",
    tags=["coffee", "farm"],
    examples=[
        "What is the yield of the Vietnam coffee farm?",
        "How much coffee does the Vietnam farm produce?",
        "What is the yield of the Vietnam coffee farm in pounds?",
        "How many pounds of coffee does the Vietnam farm produce?",
    ]
)

AGENT_CARD = AgentCard(
    name='Vietnam Coffee Farm',
    description='An AI agent that returns the yield of coffee beans in pounds for the Vietnam farm.',
    version='1.0.0',
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False,
    preferred_transport="slimrpc",
    url=f"slim://{SLIM_SERVER}/lungo/agents/{AGENT_ID}",
    additional_interfaces=[
        # point-to-point transport for direct client-agent communication
        AgentInterface(transport="slimrpc", url=f"slim://{SLIM_SERVER}/lungo/agents/{AGENT_ID}"),
        # slim-based group comm and pub/sub transport
        AgentInterface(transport="slim", url=f"slim://{SLIM_SERVER}/lungo/agents/{AGENT_ID}"),
        # nats-based pub/sub transport for broadcasting to multiple subscriber
        AgentInterface(transport="nats", url=f"nats://{NATS_SERVER}/lungo/agents/{AGENT_ID}"),
        # jsonrpc endpoint for direct client-agent communication over http
        AgentInterface(transport="jsonrpc", url=f"http://0.0.0.0:{PORT}"),
    ],
)
