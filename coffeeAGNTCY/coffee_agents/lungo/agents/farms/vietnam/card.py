# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill)

from config.config import get_agent_url

# Port configuration for this agent
PORT = 9997

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
    id='vietnam-farm-agent',
    description='An AI agent that returns the yield of coffee beans in pounds for the Vietnam farm.',
    url=get_agent_url(PORT),
    version='1.0.0',
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False,
)