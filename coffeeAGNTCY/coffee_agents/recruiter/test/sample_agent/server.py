# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""A2A server for the test agent using ADK's to_a2a utility."""

import os
from dotenv import load_dotenv
from a2a.types import AgentCard

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from test.sample_agent.agent import create_test_agent

load_dotenv()

# Server configuration
PORT = int(os.getenv("PORT", "3210"))

# Create the ADK agent
root_agent = create_test_agent()

# Define custom agent card
AGENT_CARD = AgentCard(
    name="TestAgent",
    url=f"http://localhost:{PORT}",
    description="A simple test agent for integration testing with basic tools.",
    version="1.0.0",
    capabilities={"streaming": True},
    skills=[],
    defaultInputModes=["text/plain"],
    defaultOutputModes=["text/plain"],
    supportsAuthenticatedExtendedCard=False,
)

# Create the A2A app using to_a2a utility
a2a_app = to_a2a(root_agent, port=PORT, agent_card=AGENT_CARD)

if __name__ == "__main__":
    import uvicorn
    print(f"Starting TestAgent A2A server on port {PORT}")
    uvicorn.run(a2a_app, host="0.0.0.0", port=PORT)
