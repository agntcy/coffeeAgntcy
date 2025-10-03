import asyncio
import re
import uuid
from datetime import datetime
from collections import defaultdict
from typing import DefaultDict, Sequence
from .interface import OrderStatusStore
from .models import StatusRecord

class InMemoryOrderStatusStore(OrderStatusStore):
  def __init__(self) -> None:
    self._data: DefaultDict[str, list[StatusRecord]] = defaultdict(list)
    self._lock = asyncio.Lock()

  async def record_status(self, order_id: str, agent: str, status: str) -> None:
    rec = StatusRecord(order_id, agent, status, datetime.utcnow())
    async with self._lock:
      last = self._data[order_id][-1] if self._data[order_id] else None
      if not last or (last.agent, last.status) != (agent, status):
        self._data[order_id].append(rec)

  async def get_history(self, order_id: str) -> Sequence[StatusRecord]:
    async with self._lock:
      return list(self._data.get(order_id, []))

  async def list_orders(self) -> list[str]:
    async with self._lock:
      return list(self._data.keys())

  async def seed_fake_data(self) -> None:
    async with self._lock:
      if "ORDER-FAKE-001" not in self._data:
        now = datetime.utcnow()
        self._data["ORDER-FAKE-001"] = [
          StatusRecord("ORDER-FAKE-001", "Shipping agent", "HANDOVER_TO_SHIPPER", now),
          StatusRecord("ORDER-FAKE-001", "Accountant agent", "PAYMENT_COMPLETE", now),
          StatusRecord("ORDER-FAKE-001", "Shipping agent", "DELIVERED", now),
        ]

  @staticmethod
  def extract_order_id(prompt: str) -> str:
    if not prompt:
      return str(uuid.uuid4())
    m = re.search(r"(?:order[_\s-]?id|order)\s*[:#=]\s*([A-Z0-9\-]{4,})", prompt, re.IGNORECASE)
    if m:
      return m.group(1).upper()
    return f"ORD-{str(uuid.uuid5(uuid.NAMESPACE_URL, prompt))[:8]}"

  @staticmethod
  def extract_status(prompt: str) -> str:
    if not prompt:
      return "IDLE"
    m = re.search(r"\b(HANDOVER_TO_SHIPPER|PAYMENT_COMPLETE|DELIVERED|IDLE)\b", prompt, re.IGNORECASE)
    if m:
      return m.group(1).upper()
    return "IDLE"

  @staticmethod
  def extract_agent(prompt: str) -> str:
    if not prompt:
      return "Unknown agent"
    m = re.search(r"agent\s*[:#=]\s*([\w\s]+)", prompt, re.IGNORECASE)
    if m:
      return m.group(1).strip()
    return "Unknown agent"