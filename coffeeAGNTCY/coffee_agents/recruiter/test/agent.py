# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from google.adk.agents import Agent
from agent_recruiter.recruiter import RecruiterTeam

# Create the team with full plugin support
recruiter_team = RecruiterTeam()

# Export root_agent for `adk web` / `adk run` (plugins won't work)
root_agent: Agent = recruiter_team.get_root_agent()