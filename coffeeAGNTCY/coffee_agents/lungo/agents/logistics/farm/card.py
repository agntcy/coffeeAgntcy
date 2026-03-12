# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill
)
from config.config import SLIM_SERVER

AGENT_SKILL = AgentSkill(
    id="get_farm_status",
    name="Get Farm Status",
    description="Returns the farm status of coffee beans from the farms.",
    tags=["coffee", "farm"],
    examples=[
        "What is the current farm status of my coffee order?",
        "How much coffee does the Brazil farm produce?",
        "What is the yield of the Brazil coffee farm in pounds?",
        "How many pounds of coffee does the Brazil farm produce?",
    ]
)

AGENT_CARD = AgentCard(
    name='Tatooine Farm agent',
    id='tatooine-agent',
    description='An AI agent that provides coffee beans',
    version='1.0.0',
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supports_authenticated_extended_card=False,
    preferred_transport="slim",
    url=f"slim://{SLIM_SERVER}/lungo/agents/tatooine_farm_agent",
    additional_interfaces=[
        AgentInterface(transport="slim", url=f"slim://{SLIM_SERVER}/lungo/agents/tatooine_farm_agent"),
        AgentInterface(transport="slimrpc", url=f"slim://{SLIM_SERVER}/lungo/agents/tatooine_farm_agent_rpc"),
    ],
)