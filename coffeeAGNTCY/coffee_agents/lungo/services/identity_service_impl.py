# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
from pydantic import ValidationError
import requests
from typing import Dict, Any

from identityservice.sdk import IdentityServiceSdk

from services.identity_service import IdentityService
from services.models import IdentityServiceApps, Badge

CLI_MAX_RETRIES = 3
CLI_RETRY_DELAY = 2

class IdentityServiceImpl(IdentityService):
  def __init__(self, api_key: str, base_url: str):
    self.api_key = api_key
    self.base_url = base_url

  def get_all_apps(self) -> IdentityServiceApps:
    """Fetch all apps and return them as a structured response."""
    url = f"{self.base_url}/v1alpha1/apps"
    headers = {"x-id-api-key": self.api_key}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      try:
        return IdentityServiceApps(**response.json())
      except ValidationError as e:
        raise ValueError(f"Invalid response format: {e}")
    else:
      raise ValueError(f"Failed to fetch apps: {response.status_code}, {response.text}")

  def get_badge_for_app(self, app_id: str) -> Badge:
    """Fetch the current badge issued for the specified app and return it as a Badge model."""
    url = f"{self.base_url}/v1alpha1/apps/{app_id}/badge"
    headers = {"x-id-api-key": self.api_key}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      try:
        badge = Badge(**response.json())
        return badge
      except ValidationError as e:
        raise ValueError(f"Invalid badge format: {e}")
    else:
      raise ValueError(f"Failed to fetch badge for app {app_id}: {response.status_code}, {response.text}")

  def verify_badges(self, badge: Badge) -> Dict[str, Any]:
    """Verify the provided badge data."""
    url = f"{self.base_url}/v1alpha1/badges/verify"
    headers = {
      "Content-Type": "application/json",
      "x-id-api-key": self.api_key,
    }
    data = {"badge": badge.verifiableCredential.proof.proofValue}

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
      return response.json()
    else:
      raise ValueError(f"Failed to verify badge: {response.status_code}, {response.text}")

  async def create_badge(self, agent_url: str, svc_api_key: str) -> str:
    sdk = IdentityServiceSdk(
      api_key=svc_api_key,
      async_mode=True,
    )

    for attempt in range(1, CLI_MAX_RETRIES + 1):
      try:
        await sdk.aissue_badge(agent_url)
        return 'Badge created successfully'
      except Exception as e:
        if attempt == CLI_MAX_RETRIES:
          raise ValueError(f"Failed to create badge after {CLI_MAX_RETRIES} attempts: {e}")
        await asyncio.sleep(CLI_RETRY_DELAY)
