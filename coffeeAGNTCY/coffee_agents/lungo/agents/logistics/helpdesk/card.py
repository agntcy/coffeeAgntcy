# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill)

from config.config import get_agent_url

# Port configuration for this agent
PORT = 9094


AGENT_SKILL = AgentSkill(
    id="helpdesk_support",
    name="Helpdesk Support",
    description="Provides assistance with logistics and support queries.",
    tags=["logistics", "support", "helpdesk"],
    examples=[
        "How can I track my shipment?",
        "What is the status of my order?",
        "Can you help me with a logistics issue?",
        "I need assistance with my delivery.",
    ]
)

AGENT_CARD = AgentCard(
    name='Logistics Helpdesk',
    id='logistics-helpdesk-agent',
    description='An AI agent that provides logistics and support assistance for helpdesk queries.',
    url=get_agent_url(PORT),
    version='1.0.0',
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False,
)

