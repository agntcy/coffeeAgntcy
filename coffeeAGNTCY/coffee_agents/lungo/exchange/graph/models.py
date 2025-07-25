# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field
from typing import Literal

class InventoryArgs(BaseModel):
    """Arguments for the create_order tool."""
    prompt: str = Field(
        ...,
        description="The prompt to use for the broadcast. Must be a non-empty string."
    )
    farm : Literal["brazil", "colombia", "vietnam"] = Field(
        ...,
        description="The name of the farm. Must be one of 'brazil', 'colombia', or 'vietnam'."
    )

class CreateOrderArgs(BaseModel):
    """Arguments for the create_order tool."""
    farm: Literal["brazil", "colombia", "vietnam"] = Field(
        ...,
        description="The name of the farm. Must be one of 'brazil', 'colombia', or 'vietnam'."
    )
    quantity: int = Field(
        ...,
        description="The quantity of the order. Must be a positive integer."
    )
    price: float = Field(
        ...,
        description="The price of the order. Must be a positive float."
    )
