from abc import ABC, abstractmethod

class IdentityService(ABC):
  @abstractmethod
  def get_all_apps(self):
    """Fetch all apps."""
    pass

  @abstractmethod
  def get_badge_for_app(self, app_id: str):
    """Fetch the current badge issued for the specified app."""
    pass

  @abstractmethod
  def verify_badges(self, badge: str):
    """Verify the provided badge data."""
    pass

  @abstractmethod
  async def create_badge(self, agent_url: str, api_key: str):
    """Create a badge using the identity-cli binary."""
    pass