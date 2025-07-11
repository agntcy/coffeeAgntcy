# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel

class FlavorProfileInput(BaseModel):
    """
    Represents the input for the flavor profile estimation.
    This class is used to structure the input payload for the A2A agent.
    """
    prompt: str

class FlavorProfileOutput(BaseModel):
    """
    Represents the output of the flavor profile estimation.
    This class is used to structure the response from the A2A agent.
    """
    flavor_profile: str
