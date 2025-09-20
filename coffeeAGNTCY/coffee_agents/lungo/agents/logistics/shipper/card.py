# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import (
    AgentCapabilities, 
    AgentCard,
    AgentSkill)

AGENT_SKILL = AgentSkill(
    id="get_shipping_status",
    name="Get Shipping Status",
    description="Returns the shipping status of coffee beans from the farms.",
    tags=["coffee", "shipping"],
    examples=[
        "Advance the order from HANDOVER_TO_SHIPPER to CUSTOMS_CLEARANCE.",
        "Has the shipment moved past HANDOVER_TO_SHIPPER yet?",
        "Did the Brazil farm order reach CUSTOMS_CLEARANCE?",
        "After payment, confirm the shipment is DELIVERED.",
        "Mark the Colombia 50 lb order as DELIVERED if payment is complete.",
        "What is the current shipping status of my last coffee order?",
        "Has the order been delivered following PAYMENT_COMPLETE?",
    ]
)   

AGENT_CARD = AgentCard(
    name='Shipping agent',
    id='shipping-agent',
    description='An AI agent that ships coffee beans and sends status updates.',
    url='',
    version='1.0.0',
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False,
)