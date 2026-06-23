# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)
from config.config import FARM_AGENT_HOST, FARM_AGENT_PORT, NATS_SERVER, SLIM_SERVER

AGENT_ID = "flavor-profile-farm-agent"
SLIM_TOPIC = f"default/default/{AGENT_ID}"

AGENT_SKILL = AgentSkill(
    id="estimate_flavor",
    name="Estimate Flavor Profile",
    description="Analyzes a natural language prompt and returns the expected flavor profile for a coffee-growing region and/or season.",
    tags=["coffee", "flavor", "farm"],
    examples=[
        "What flavors can I expect from coffee in Huila during harvest?",
        "Describe the taste of beans grown in Sidamo in the dry season",
        "How does Yirgacheffe coffee taste?",
    ],
)

AGENT_CARD = AgentCard(
    name="Coffee Farm Flavor Agent",
    id=AGENT_ID,
    description="An AI agent that estimates the flavor profile of coffee beans using growing conditions like season and altitude.",
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False,
    preferred_transport="slim",
    url=f"slim://{SLIM_SERVER}/{SLIM_TOPIC}",
    additional_interfaces=[
        AgentInterface(
            transport="slim",
            url=f"slim://{SLIM_SERVER}/{SLIM_TOPIC}",
        ),
        AgentInterface(
            transport="jsonrpc",
            url=f"http://{FARM_AGENT_HOST}:{FARM_AGENT_PORT}/",
        ),
        AgentInterface(
            transport="nats",
            url=f"nats://{NATS_SERVER}/{SLIM_TOPIC}",
        ),
    ],
)
