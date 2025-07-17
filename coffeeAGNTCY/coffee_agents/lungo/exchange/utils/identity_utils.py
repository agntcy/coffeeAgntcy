# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import uuid
import logging
from exchange.service.hydra_client_service_impl import HydraClientServiceImpl
from exchange.service.identity_service_impl import IdentityServiceImpl

logger = logging.getLogger("lungo.supervisor.identity_utils")

# key = farm name, value = client_id
farm_client_id_map = {}

def initialize_clients_and_issue_badges(hydra_admin_url, idp_url, farm_agent_urls: dict, register_issuer=False, identity_api_url=None):
  """
  Initialize clients, process badge workflows, and cache client IDs.

  Args:
      hydra_admin_url (str): URL of the Hydra Admin API.
      idp_url (str): Identity Provider URL.
      farm_agent_urls (dict): List of farm agent URLs.
      register_issuer (bool): Flag to indicate whether to register the issuer in the first iteration.
      identity_api_url (str, optional): URL of the identity API. Defaults to None.

  Returns:
      dict: A cache containing client IDs mapped to their respective farm agent URLs.
  """
  global farm_client_id_map  # Use the global cache
  try:
    hydra_service = HydraClientServiceImpl(hydra_admin_url)
    farm_client_id_map.clear()  # Clear the cache before initializing

    first_iteration = True
    for farm_agent_name, farm_agent_url in farm_agent_urls.items():
      logger.info(f"Processing farm agent: {farm_agent_name} at {farm_agent_url}")
      client_id = f"client-{uuid.uuid4().hex[:5]}"
      client_secret = f"secret-{uuid.uuid4().hex[:5]}"

      # Create OAuth client
      client = hydra_service.create_oauth_client(client_id, client_secret)
      farm_client_id_map[farm_agent_name] = client["client_id"]

      # Initialize and process badge workflow
      identity_service = IdentityServiceImpl(
        idp_url=idp_url,
        client_id=client["client_id"],
        client_secret=client["client_secret"],
        farm_agent_url=farm_agent_url,
        identity_api_url=identity_api_url,
      )

      # If it's the first iteration, connect to vault and register issuer
      if first_iteration and register_issuer:
        identity_service.connect_vault()
        identity_service.generate_vault_key()
        identity_service.register_issuer()

      identity_service.generate_metadata()
      identity_service.issue_badge()
      identity_service.publish_badge()

      first_iteration=False

    return farm_client_id_map
  except Exception as e:
    logger.error(f"Error initializing clients and issuing badges: {e}")
    farm_client_id_map.clear()  # Clear cache on error
    return {}