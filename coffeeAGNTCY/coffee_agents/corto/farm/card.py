# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill)
from config.config import FARM_AGENT_HOST, FARM_AGENT_PORT

AGENT_SKILL = AgentSkill(
    id="estimate_flavor",
    name="Estimate Flavor Profile",
    description="Analyzes a natural language prompt and returns the expected flavor profile for a coffee-growing region and/or season.",
    tags=["coffee", "flavor", "farm"],
    examples=[
        "What flavors can I expect from coffee in Huila during harvest?",
        "Describe the taste of beans grown in Sidamo in the dry season",
        "How does Yirgacheffe coffee taste?"
    ]
)

AGENT_CARD = AgentCard(
    name='Coffee Farm Flavor Agent',
    id='flavor-profile-farm-agent',
    description='An AI agent that estimates the flavor profile of coffee beans using growing conditions like season and altitude.',
    url=f'http://{FARM_AGENT_HOST}:{FARM_AGENT_PORT}/',
    version='1.0.0',
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False,
)
