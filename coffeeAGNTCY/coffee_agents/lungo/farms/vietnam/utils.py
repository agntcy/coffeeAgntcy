# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
import os


from services.identity_service_impl import IdentityServiceImpl
from services.identity_service_oss_impl import IdentityServiceOSSImpl

from config.config import (
  IDENTITY_VIETNAM_AGENT_SERVICE_API_KEY,
  VIETNAM_FARM_AGENT_URL,
  IDENTITY_API_KEY,
  IDENTITY_API_SERVER_URL,
  HYDRA_ADMIN_URL
)

logger = logging.getLogger("vietnam.utils")

async def create_badge_for_vietnam_farm():
  """Create a badge after the HTTP server starts and is ready."""
  svc_api_key = IDENTITY_VIETNAM_AGENT_SERVICE_API_KEY
  try:
    # Proceed to create the badge
    if os.getenv("ENABLE_OSS_IDENTITY", False):
      logger.info("OSS Identity is enabled.")
      identity_service = IdentityServiceOSSImpl(
        idp_url=os.getenv("IDP_ISSUER_URL"),
        hydra_admin_url= HYDRA_ADMIN_URL,
        agent_url=VIETNAM_FARM_AGENT_URL,
        identity_api_url=os.getenv("IDENTITY_API_SERVER_URL")
      )
      svc_api_key = "fake-key-for-oss"
    else:
      identity_service = IdentityServiceImpl(api_key=IDENTITY_API_KEY,
                                             base_url=IDENTITY_API_SERVER_URL)
    await identity_service.create_badge(agent_url=VIETNAM_FARM_AGENT_URL,
                                                 api_key=svc_api_key)
    logger.info("Creating badge for Vietnam farm")
  except Exception as e:
    print("Failed to create badge:", e)
