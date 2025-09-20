# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import (
    AgentCapabilities, 
    AgentCard,
    AgentSkill)

AGENT_SKILL = AgentSkill(
    id="get_accounting_status",
    name="Get Accounting Status",
    description="Returns the accounting / payment status of coffee bean orders.",
    tags=["coffee", "accounting", "payments"],
    examples=[
        "Has the order moved from CUSTOMS_CLEARANCE to PAYMENT_COMPLETE yet?",
        "Confirm payment completion for the Colombia shipment.",
        "Did the Brazil order clear CUSTOMS_CLEARANCE and get marked PAYMENT_COMPLETE?",
        "Is any payment still pending after CUSTOMS_CLEARANCE?",
        "Mark the 50 lb Colombia order as PAYMENT_COMPLETE if customs is cleared.",
    ]
)

AGENT_CARD = AgentCard(
    name='Accountant agent',
    id='accountant-agent',
    description='An AI agent that confirms the payment.',
    url='',
    version='1.0.0',
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False,
)