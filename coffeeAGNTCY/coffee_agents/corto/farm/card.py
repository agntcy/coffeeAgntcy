# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill)

from config.config import FARM_AGENT_HOST, FARM_AGENT_PORT

AGENT_SKILL = AgentSkill(
    id="estimate_flavor",
    name="Estimate Flavor Profile",
    description="Analyzes a natural language prompt and returns the expected flavor profile for a coffee-growing region and/or season.",
    tags=["coffee", "flavor", "farm"],
    examples=[
        "What flavors can I expect from coffee in Huila during harvest?",
        "Describe the taste of beans grown in Sidamo in the dry season",
        "How does Yirgacheffe coffee taste?"
    ]
)

AGENT_CARD = AgentCard(
    name='Coffee Farm Flavor Agent',
    id='flavor-profile-farm-agent',
    description='An AI agent that estimates the flavor profile of coffee beans using growing conditions like season and altitude.',
    url=f'http://{FARM_AGENT_HOST}:{FARM_AGENT_PORT}/',
    version='1.0.0',
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False,
)
