# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod

class HydraClientService(ABC):
  """Interface for managing Hydra clients."""

  @abstractmethod
  def create_oauth_client(self, client_id: str, client_secret: str) -> dict:
    """Create a new client in Hydra."""
    pass
