import abc
from typing import Sequence
from .models import StatusRecord

class OrderStatusStore(abc.ABC):
  @abc.abstractmethod
  async def record_status(self, order_id: str, agent: str, status: str) -> None: ...
  @abc.abstractmethod
  async def get_history(self, order_id: str) -> Sequence[StatusRecord]: ...
  @abc.abstractmethod
  async def list_orders(self) -> list[str]: ...
