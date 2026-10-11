# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os

import config.config
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

PORT = os.getenv("QC_AGENT_PORT", "9996")
AGENT_ID = "quality_control_agent"

AGENT_SKILL = AgentSkill(
    id="assess_quality",
    name="Assess Coffee Quality",
    description=(
        "Grades a farm's green coffee lot from cupping score, defect rate and "
        "moisture, and returns a 0-100 quality score, a grade (A/B/C/FAIL) and "
        "an inspector's note."
    ),
    tags=["coffee", "quality", "evaluator"],
    examples=[
        "Assess the quality of the Colombia farm's coffee.",
        "Give me a quality report for all farms.",
        "Does the Vietnam lot pass quality control?",
    ],
)

AGENT_CARD = AgentCard(
    name="Quality Control Agent",
    description="An AI agent that grades the quality of each farm's coffee lot.",
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
