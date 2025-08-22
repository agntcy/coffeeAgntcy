# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import requests
import logging

from services.hydra_client_service import HydraClientService


class HydraClientServiceImpl(HydraClientService):
  """Implementation of the HydraClientService interface."""

  def __init__(self, hydra_admin_url: str):
    self.hydra_admin_url = hydra_admin_url

  def create_oauth_client(self, client_id: str, client_secret: str) -> dict:
    """Create a new client in Hydra."""

    client_data = {
      "grant_types": ["client_credentials"],
      "client_id": client_id,
      "client_secret": client_secret
    }

    response = requests.post(self.hydra_admin_url, json=client_data)

    if response.status_code == 201:
      return response.json()
    elif response.status_code == 409:
      logging.warning(f"Client already exists. Status: {response.status_code}, Error: {response.text}")
      return {"message": "Client already exists"}
    else:
      raise Exception(
        f"Failed to create client. Status: {response.status_code}, Error: {response.text}"
      )