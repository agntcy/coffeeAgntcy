# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import abc
from typing import Sequence, List, Tuple, Optional
from .event import OrderEvent


class OrderEventStore(abc.ABC):
  """
  Event store with atomic append + index based waiting.
  Index == current number of events already observed.
  """

  @abc.abstractmethod
  async def set(self, order_id: str, events: Sequence[OrderEvent]) -> None:
    ...

  @abc.abstractmethod
  async def get(self, order_id: str) -> List[OrderEvent]:
    ...

  @abc.abstractmethod
  async def append(self, order_id: str, event: OrderEvent) -> int:
    """
    Append one event. Return new length (next index baseline).
    """

  @abc.abstractmethod
  async def delete(self, order_id: str) -> None:
    ...

  @abc.abstractmethod
  async def wait_for_events(
          self,
          order_id: str,
          last_index: int,
          timeout: Optional[float] = None,
  ) -> Tuple[List[OrderEvent], int]:
    """
    Block until list length > last_index or timeout.
    Return (new_events, new_index). If timeout: ([], last_index).
    """
    ...
