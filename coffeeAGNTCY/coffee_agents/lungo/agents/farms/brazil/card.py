# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill)

from config.config import get_agent_url

# Port configuration for this agent
PORT = 9999

AGENT_SKILL = AgentSkill(
    id="get_yield",
    name="Get Coffee Yield",
    description="Returns the coffee farm's yield in lb.",
    tags=["coffee", "farm"],
    examples=[
        "What is the yield of the Brazil coffee farm?",
        "How much coffee does the Brazil farm produce?",
        "What is the yield of the Brazil coffee farm in pounds?",
        "How many pounds of coffee does the Brazil farm produce?",
    ]
)   

AGENT_CARD = AgentCard(
    name='Brazil Coffee Farm',
    id='brazil-farm-agent',
    description='An AI agent that returns the yield of coffee beans in pounds for the Brazil farm.',
    url=get_agent_url(PORT),
    version='1.0.0',
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False,
)