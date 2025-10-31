# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field
from typing import Literal

class CreateOrderArgs(BaseModel):
  """Arguments for the create_order tool."""
  farm: Literal["tatooine"] = Field(
    ...,
    description="The name of the farm. Must be 'tatooine'."
  )
  quantity: int = Field(
    ...,
    description="The quantity of the order. Must be a positive integer."
  )
  price: float = Field(
    ...,
    description="The price of the order. Must be a positive float."
  )
