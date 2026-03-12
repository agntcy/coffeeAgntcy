# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Literal
from pydantic import BaseModel, Field

from agents.supervisors.auction.graph.shared import farm_registry

# Derive the allowed farm values from the registry so adding a farm
# only requires a new register() call in shared.py.
FARM_SLUGS = tuple(farm_registry.slugs())  # e.g. ("brazil", "colombia", "vietnam")
FarmLiteral = Literal[FARM_SLUGS]  # type: ignore[valid-type]

class InventoryArgs(BaseModel):
    """Arguments for the inventory tool."""
    prompt: str = Field(
        ...,
        description="The prompt to use for the broadcast. Must be a non-empty string."
    )
    farm: FarmLiteral = Field(  # type: ignore[valid-type]
        ...,
        description=f"The name of the farm. Must be one of: {', '.join(FARM_SLUGS)}."
    )

class CreateOrderArgs(BaseModel):
    """Arguments for the create_order tool."""
    farm: FarmLiteral = Field(  # type: ignore[valid-type]
        ...,
        description=f"The name of the farm. Must be one of: {', '.join(FARM_SLUGS)}."
    )
    quantity: int = Field(
        ...,
        description="The quantity of the order. Must be a positive integer."
    )
    price: float = Field(
        ...,
        description="The price of the order. Must be a positive float."
    )
