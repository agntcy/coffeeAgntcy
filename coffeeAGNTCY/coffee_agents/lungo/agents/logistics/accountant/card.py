# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import (
    AgentCapabilities, 
    AgentCard,
    AgentSkill)

AGENT_SKILL = AgentSkill(
    id="get_accounting_status",
    name="Get Accounting Status",
    description="Returns the accounting status of coffee beans from the farms.",
    tags=["coffee", "accounting"],
    examples=[
        "What is the current accounting status of my coffee order?",
        "How much coffee does the Brazil farm produce?",
        "What is the yield of the Brazil coffee farm in pounds?",
        "How many pounds of coffee does the Brazil farm produce?",
    ]
)   

AGENT_CARD = AgentCard(
    name='Accountant agent',
    id='accountant-agent',
    description='An AI agent that ships coffee beans and sends account updates.',
    url='',
    version='1.0.0',
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False,
)