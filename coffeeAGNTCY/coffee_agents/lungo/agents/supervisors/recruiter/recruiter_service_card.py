# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os

from a2a.types import AgentCard
from dotenv import load_dotenv

load_dotenv()

RECRUITER_AGENT_URL = os.getenv("RECRUITER_AGENT_URL", "http://localhost:8881")

# Define A2A agent card
RECRUITER_AGENT_CARD = AgentCard(
    name="RecruiterAgent",
    url=RECRUITER_AGENT_URL,
    description="An agent that helps find and recruit other agents based on specified criteria.",
    version="1.0.0",
    capabilities={"streaming": True},
    skills=[],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    supports_authenticated_extended_card=False,
    examples=[],
)