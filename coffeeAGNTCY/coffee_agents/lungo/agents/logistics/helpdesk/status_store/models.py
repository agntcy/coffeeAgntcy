from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(slots=True)
class StatusRecord:
  order_id: str
  agent: str
  status: str
  timestamp: datetime