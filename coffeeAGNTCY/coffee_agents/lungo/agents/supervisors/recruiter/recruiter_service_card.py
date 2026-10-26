# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os

from a2a.types import AgentCapabilities, AgentCard, AgentInterface
from dotenv import load_dotenv

load_dotenv()

RECRUITER_AGENT_URL = os.getenv("RECRUITER_AGENT_URL", "http://localhost:8881")

# Define A2A agent card. The recruiter service still speaks A2A v0.3 JSON-RPC
# (message/send, message/stream); protocol_version "0.3" makes the a2a-sdk 1.x
# ClientFactory pick its v0.3 compat transport for this interface.
RECRUITER_AGENT_CARD = AgentCard(
    name="RecruiterAgent",
    description="An agent that helps find and recruit other agents based on specified criteria.",
    version="1.0.0",
    supported_interfaces=[
        AgentInterface(
            protocol_binding="JSONRPC",
            url=RECRUITER_AGENT_URL,
            protocol_version="0.3",
        )
    ],
    capabilities=AgentCapabilities(streaming=True),
    skills=[],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
)
