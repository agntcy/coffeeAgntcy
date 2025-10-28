# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Any
from services.models import IdentityServiceApps, Badge

class IdentityService(ABC):
  @abstractmethod
  def get_all_apps(self) -> IdentityServiceApps:
    """Fetch all apps registered with the identity service."""
    pass

  @abstractmethod
  def get_badge_for_app(self, app_id: str) -> Badge:
    """Fetch the current badge issued for the specified app."""
    pass

  @abstractmethod
  def verify_badges(self, badge: Badge):
    """Verify the provided badge data with the identity service."""
    pass

  @abstractmethod
  async def create_badge(self, agent_url: str, api_key: str):
    """Discover an agent/service and request badge issuance."""
    pass

  @abstractmethod
  def get_access_token(self, svc_api_key: str) -> str:
    """
    Obtain an access (bearer) token representing the caller service identity.
    The returned token is later supplied to authorize() when requesting a tool
    invocation on another (target) service.
    """
    pass

  @abstractmethod
  def authorize(self, svc_api_key: str, access_token: str, tool_name: str) -> Any:
    """Request authorization to invoke a specific tool on a target (callee) service."""
    pass
