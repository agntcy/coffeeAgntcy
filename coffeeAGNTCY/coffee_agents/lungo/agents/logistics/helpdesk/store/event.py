# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timezone
from pydantic import BaseModel


class OrderEvent(BaseModel):
  order_id: str
  sender: str
  receiver: str
  message: str
  state: str
  timestamp: datetime = datetime.now(timezone.utc)
