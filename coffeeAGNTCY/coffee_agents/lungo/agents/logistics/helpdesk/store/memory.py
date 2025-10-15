# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
from typing import Dict, List, Optional, Sequence, Tuple

from .base import OrderEventStore
from .event import OrderEvent


# Type alias for (sequence_number, order_id) entries.
NewOrderEntry = Tuple[int, str]


class InMemoryOrderEventStore(OrderEventStore):
  """
  In-memory implementation of OrderEventStore.

  Features:
    - Stores ordered lists of OrderEvent per order_id.
    - Assigns a monotonically increasing sequence number the first time
      an order_id receives an event (order creation order).
    - Provides awaitable methods to wait for:
        * additional events on an existing order (wait_for_events)
        * creation of newer orders (wait_for_new_orders)
    - Exposes the latest created order (latest_order).
  Thread safety: relies on a single asyncio loop; guarded by asyncio.Condition.
  """

  def __init__(self) -> None:
    self._data: Dict[str, List[OrderEvent]] = {}
    self._cond = asyncio.Condition()
    self._order_seq: int = 0  # Monotonic sequence for order creation.
    self._new_orders: List[NewOrderEntry] = []  # History of (seq, order_id).

  async def set(self, order_id: str, events: Sequence[OrderEvent]) -> None:
    """
    Replace the full event list for an order_id.
    Notifies waiters only if new events appended or order newly created.
    """
    async with self._cond:
      is_new = order_id not in self._data
      existing = self._data.get(order_id, [])
      if (
              existing
              and len(events) >= len(existing)
              and list(events[: len(existing)]) == existing
      ):
        # Proper append(s) scenario; extract only the new tail.
        new_tail = list(events[len(existing) :])
      else:
        # Replace or divergent history; treat entire list as new content.
        new_tail = list(events)

      self._data[order_id] = list(events)

      if is_new and events:
        self._order_seq += 1
        self._new_orders.append((self._order_seq, order_id))

      if is_new or new_tail:
        self._cond.notify_all()

  async def get(self, order_id: str) -> List[OrderEvent]:
    """
    Return a shallow copy of the event list for order_id (empty if unknown).
    """
    async with self._cond:
      return list(self._data.get(order_id, []))

  async def append(self, order_id: str, event: OrderEvent) -> int:
    """
    Append a single event. Returns new length of the order's event list.
    """
    async with self._cond:
      is_new = order_id not in self._data
      lst = self._data.setdefault(order_id, [])
      lst.append(event)
      if is_new:
        self._order_seq += 1
        self._new_orders.append((self._order_seq, order_id))
      self._cond.notify_all()
      return len(lst)

  async def delete(self, order_id: str) -> None:
    """
    Remove all events for an order_id (no sequence rewinding).
    """
    async with self._cond:
      if order_id in self._data:
        del self._data[order_id]
        self._cond.notify_all()

  async def wait_for_events(
          self,
          order_id: str,
          last_index: int,
          timeout: Optional[float] = None,
  ) -> Tuple[List[OrderEvent], int]:
    """
    Wait until events beyond last_index exist for order_id or timeout.

    Returns:
      (new_events, new_total_length)
      new_events empty if timed out or no change.
    """
    async with self._cond:
      def changed() -> bool:
        return len(self._data.get(order_id, [])) > last_index

      if not changed():
        if timeout is None:
          await self._cond.wait_for(changed)
        else:
          try:
            await asyncio.wait_for(self._cond.wait_for(changed), timeout)
          except asyncio.TimeoutError:
            return [], last_index

      full = self._data.get(order_id, [])
      new_events = full[last_index:]
      return list(new_events), len(full)

  async def wait_for_new_orders(
          self,
          last_seq: int,
          timeout: Optional[float] = None,
  ) -> Tuple[List[NewOrderEntry], int]:
    """
    Wait until at least one new order (sequence > last_seq) appears or timeout.

    Returns:
      (list_of_new (seq, order_id), latest_seq_after_check)
      list empty if timed out or no new orders.
    """
    async with self._cond:
      def changed() -> bool:
        return self._order_seq > last_seq

      if not changed():
        if timeout is None:
          await self._cond.wait_for(changed)
        else:
          try:
            await asyncio.wait_for(self._cond.wait_for(changed), timeout)
          except asyncio.TimeoutError:
            return [], last_seq

      result = [pair for pair in self._new_orders if pair[0] > last_seq]
      return result, self._order_seq

  async def latest_order(self) -> Optional[NewOrderEntry]:
    """
    Return the most recently created order as (seq, order_id) or None.
    """
    async with self._cond:
      return self._new_orders[-1] if self._new_orders else None
