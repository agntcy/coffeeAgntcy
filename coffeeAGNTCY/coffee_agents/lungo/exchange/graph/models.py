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

from pydantic import BaseModel

class GetFarmYieldInput(BaseModel):
    """
    Represents the input for the get farm yield agent call.
    This class is used to structure the input payload for the A2A agent.
    """
    farm_name: str

class GetFarmYieldOutput(BaseModel):
    """
    Represents the output for the get farm yield agent call.
    This class is used to structure the response from the A2A agent.
    """
    yields: dict[str, float] # Mapping of farm names to their yields in pounds

class FetchHarvestInput(BaseModel):
    """
    Represents the input for the fetch harvest agent call.
    This class is used to structure the input payload for the A2A agent.
    """
    prompt: str

class FetchHarvestOutput(BaseModel):
    """
    Represents the output of the fetch harvest agent call.
    This class is used to structure the response from the A2A agent.
    """
    yield_lb: str
