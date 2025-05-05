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

from enum import Enum
from typing import Optional, TypedDict

from pydantic import BaseModel, Field

class ConfigSchema(TypedDict):
    pass

class MsgType(Enum):
    human = "human"
    assistant = "assistant"

class Message(BaseModel):
    type: MsgType = Field(
        ...,
        description="indicates the originator of the message, a human or an assistant",
    )
    content: str = Field(..., description="the content of the message")

class InputState(BaseModel):
    messages: Optional[list[Message]] = None

class OutputState(BaseModel):
    messages: Optional[list[Message]] = None

class AgentState(BaseModel):
    agent_input: InputState
    agent_output: Optional[OutputState] = None
