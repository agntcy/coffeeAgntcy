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

from typing import Annotated, Literal, TypedDict
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.types import Command
from langgraph.constants import END
import logging

SAMPLE_RESPONSE = "Need 100 tons of Arabica roast from Vietnam region by December 15"

class Router(TypedDict):
  next: Annotated[Literal["node_agp_boardcast", "FINISH"], ...]
  reasoning: Annotated[str, ...]

def supervisor_node(state: AgentState) -> Command:
  response = Router(
    next="node_agp_boardcast",
    reasoning=SAMPLE_RESPONSE,
  )

  goto = response["next"]

  if goto == "FINISH":
    logging.info("FINISH")
    goto = END

  logging.info(f"goto: {goto}")
  return Command(goto=goto, update={"next": goto, "reasoning": response["reasoning"]})
