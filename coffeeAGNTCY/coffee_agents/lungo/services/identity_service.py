# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from services.models import IdentityServiceApps, Badge

class IdentityService(ABC):
  @abstractmethod
  def get_all_apps(self) -> IdentityServiceApps:
    """Fetch all apps."""
    pass

  @abstractmethod
  def get_badge_for_app(self, app_id: str) -> Badge:
    """Fetch the current badge issued for the specified app."""
    pass

  @abstractmethod
  def verify_badges(self, badge: Badge):
    """Verify the provided badge data."""
    pass

  @abstractmethod
  async def create_badge(self, agent_url: str, api_key: str):
    """Create a badge."""
    pass
