# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging

from config.config import (
  IDENTITY_VIETNAM_AGENT_SERVICE_API_KEY,
  VIETNAM_FARM_AGENT_URL,
  IDENTITY_API_KEY,
  IDENTITY_API_SERVER_URL,
)
from services.identity_service_impl import IdentityServiceImpl

logger = logging.getLogger("vietnam.utils")

async def create_badge_for_vietnam_farm():
  """Create a badge after the HTTP server starts and is ready."""
  try:
    # Proceed to create the badge
    identity_service = IdentityServiceImpl(api_key=IDENTITY_API_KEY,
                                           base_url=IDENTITY_API_SERVER_URL)
    badge_output = await identity_service.create_badge(agent_url=VIETNAM_FARM_AGENT_URL,
                                                 svc_api_key=IDENTITY_VIETNAM_AGENT_SERVICE_API_KEY)
    logger.info("Creating badge for Vietnam farm: %s", badge_output)
  except Exception as e:
    print("Failed to create badge:", e)
