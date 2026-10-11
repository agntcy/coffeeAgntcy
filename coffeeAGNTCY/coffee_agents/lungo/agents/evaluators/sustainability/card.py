# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os

import config.config
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

PORT = os.getenv("SUSTAINABILITY_AGENT_PORT", "9995")
AGENT_ID = "sustainability_agent"

AGENT_SKILL = AgentSkill(
    id="assess_sustainability",
    name="Assess Farm Sustainability",
    description=(
        "Rates a farm's environmental impact from certifications, shipping CO2, "
        "deforestation risk and water use, and returns a 0-100 sustainability "
        "score, a grade (A/B/C/FAIL) and an auditor's note."
    ),
    tags=["coffee", "sustainability", "evaluator"],
    examples=[
        "How sustainable is the Brazil farm?",
        "Give me a sustainability report for all farms.",
        "Does the Vietnam farm pass the sustainability audit?",
    ],
)

AGENT_CARD = AgentCard(
    name="Sustainability Agent",
    description="An AI agent that audits the environmental impact of each coffee farm.",
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False,
    preferred_transport="slim",
    url=f"slim://{config.config.SLIM_SERVER}/lungo/agents/{AGENT_ID}",
    additional_interfaces=[
        AgentInterface(
            transport="slim",
            url=f"slim://{config.config.SLIM_SERVER}/lungo/agents/{AGENT_ID}",
        ),
        AgentInterface(
            transport="nats",
            url=f"nats://{config.config.NATS_SERVER}/lungo/agents/{AGENT_ID}",
        ),
        AgentInterface(transport="jsonrpc", url=f"http://0.0.0.0:{PORT}"),
    ],
)
