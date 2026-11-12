# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from dotenv import load_dotenv

load_dotenv()

RECRUITER_AGENT_URL = os.getenv("RECRUITER_AGENT_URL", "http://localhost:8881")

# Define A2A agent card. The recruiter service is an a2a-sdk 1.x server that
# speaks A2A v1.0 only. protocol_version "1.0" makes the a2a-sdk 1.x
# ClientFactory speak A2A v1.0 JSON-RPC to it. This needs the recruiter image
# built from the a2a-sdk 1.x port: the older published image is an a2a 0.3
# server and does not answer v1.0 requests.
RECRUITER_AGENT_CARD = AgentCard(
    name="RecruiterAgent",
    description="An agent that helps find and recruit other agents based on specified criteria.",
    version="1.0.0",
    supported_interfaces=[
        AgentInterface(
            protocol_binding="JSONRPC",
            url=RECRUITER_AGENT_URL,
            protocol_version="1.0",
        )
    ],
    capabilities=AgentCapabilities(streaming=True),
    # a2a-sdk 1.2 warns when a card has no skills.
    skills=[
        AgentSkill(
            id="recruit_agents",
            name="Recruit agents",
            description="Search the agent directory for agents that match a task and evaluate them against scenarios.",
            tags=["recruiting", "agents", "evaluation"],
        )
    ],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
)
