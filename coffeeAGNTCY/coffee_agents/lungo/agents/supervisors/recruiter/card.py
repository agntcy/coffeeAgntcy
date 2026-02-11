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
    id="recruiter-supervisor-agent",
    description=(
        "An AI supervisor that recruits agents from the AGNTCY directory "
        "and dynamically delegates tasks to them."
    ),
    url="",
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[RECRUITER_SUPERVISOR_SKILL],
    supportsAuthenticatedExtendedCard=False,
)
