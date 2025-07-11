# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import uuid
import logging
from exchange.service.hydra_client_service_impl import HydraClientServiceImpl
from exchange.service.identity_service_impl import IdentityServiceImpl

logger = logging.getLogger("lungo.supervisor.identity_utils")

# Define the global client cache
client_cache = {}

def initialize_clients_and_issue_badges(hydra_admin_url, idp_url, farm_agent_urls, register_issuer=False, identity_api_url=None):
  """
  Initialize clients, process badge workflows, and cache client IDs.

  Args:
      hydra_admin_url (str): URL of the Hydra Admin API.
      idp_url (str): Identity Provider URL.
      farm_agent_urls (list): List of farm agent URLs.
      register_issuer (bool): Flag to indicate whether to register the issuer in the first iteration.
      identity_api_url (str, optional): URL of the identity API. Defaults to None.

  Returns:
      dict: A cache containing client IDs mapped to their respective farm agent URLs.
  """
  global client_cache  # Use the global cache
  try:
    hydra_service = HydraClientServiceImpl(hydra_admin_url)
    client_cache.clear()  # Clear the cache before initializing

    for i, farm_agent_url in enumerate(farm_agent_urls, start=1):
      client_id = f"client-{uuid.uuid4().hex[:5]}"
      client_secret = f"secret-{uuid.uuid4().hex[:5]}"

      # Create OAuth client
      client = hydra_service.create_oauth_client(client_id, client_secret)
      client_cache[farm_agent_url] = client["client_id"]

      # Initialize and process badge workflow
      identity_service = IdentityServiceImpl(
        idp_url=idp_url,
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        farm_agent_url=farm_agent_url,
        identity_api_url=identity_api_url,
      )

      # If it's the first iteration, connect to vault and register issuer
      if i == 1 and register_issuer:
        identity_service.connect_vault()
        identity_service.generate_vault_key()
        identity_service.register_issuer()

      identity_service.generate_metadata()
      identity_service.issue_badge()
      identity_service.publish_badge()

    return client_cache
  except Exception as e:
    logger.error(f"Error initializing clients and issuing badges: {e}")
    client_cache.clear()  # Clear cache on error
    return {}