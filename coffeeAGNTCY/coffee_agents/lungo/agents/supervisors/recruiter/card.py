# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from a2a.types import AgentCapabilities, AgentCard, AgentSkill

RECRUITER_SUPERVISOR_SKILL = AgentSkill(
    id="recruit_and_delegate",
    name="Recruit and Delegate",
    description=(
        "Searches the AGNTCY directory for agents matching a task description, "
        "recruits them, and dynamically delegates tasks to the recruited agents."
    ),
    tags=["recruiter", "agents", "delegation"],
    examples=[
        "Find me an agent that can handle accounting tasks",
        "Search for agents with shipping capabilities and evaluate them",
        "Execute the accounting task using the recruited agent",
    ],
)

RECRUITER_SUPERVISOR_CARD = AgentCard(
    name="Recruiter Supervisor",
    description=(
        "An AI supervisor that recruits agents from the AGNTCY directory "
        "and dynamically delegates tasks to them."
    ),
    version="1.0.0",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[RECRUITER_SUPERVISOR_SKILL],
    # Caller identity only: this supervisor serves no A2A interface.
    supported_interfaces=[],
)
