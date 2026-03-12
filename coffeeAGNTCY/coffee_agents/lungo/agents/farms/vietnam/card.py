# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os
from a2a.types import (
    AgentCapabilities, 
    AgentCard,
    AgentInterface,
    AgentSkill
)
from config.config import PREFERRED_A2A_TRANSPORT, SLIM_SERVER, NATS_SERVER

PORT = os.getenv("FARM_AGENT_PORT", "9997")

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
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supports_authenticated_extended_card=False,

    preferred_transport=PREFERRED_A2A_TRANSPORT,
    url='', # will be set dynamically based on the preferred transport's additional interface url
    additional_interfaces=[
        # point-to-point transport for direct client-agent communication
        AgentInterface(transport="slimrpc", url=f"slim://{SLIM_SERVER}/lungo/agents/vietnam_coffee_farm"),
        # slim-based group comm and pub/sub transport
        AgentInterface(transport="slim", url=f"slim://{SLIM_SERVER}/lungo/agents/farm_broadcast"),
        # nats-based pub/sub transport for broadcasting to multiple subscriber
        AgentInterface(transport="nats", url=f"nats://{NATS_SERVER}/lungo/agents/farm_broadcast"),
        # jsonrpc endpoint for direct client-agent communication over http
        AgentInterface(transport="jsonrpc", url=f"http://0.0.0.0:{PORT}"), 
    ],
)

# Set url to match the preferred transport's interface
_preferred = next(
    (i for i in (AGENT_CARD.additional_interfaces or []) if i.transport == AGENT_CARD.preferred_transport),
    None,
)
if _preferred:
    AGENT_CARD.url = _preferred.url
else:
    raise ValueError(
        f"preferred_transport {PREFERRED_A2A_TRANSPORT!r} not found in additional_interfaces. "
        f"Available: {[i.transport for i in (AGENT_CARD.additional_interfaces or [])]}"
    )