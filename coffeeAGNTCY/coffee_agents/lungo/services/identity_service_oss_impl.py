# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import uuid
import os
import logging
import asyncio
from typing import Dict, Any
from services.identity_service import IdentityService
from services.hydra_client_service_impl import HydraClientServiceImpl
from services.models import IdentityServiceApps, IdentityServiceApp, Badge
from agntcyidentity.sdk import IdentitySdk
from config.config import VIETNAM_FARM_AGENT_URL, COLOMBIA_FARM_AGENT_URL
from farms.colombia.card import AGENT_CARD as colombia_agent_card
from farms.vietnam.card import AGENT_CARD as vietnam_agent_card

logger = logging.getLogger("lungo.services.identity_service_oss")

# Mapping farm agent URLs to their respective card names, and client IDs (slugs)
CARD_URL_MAP = {
  VIETNAM_FARM_AGENT_URL: (vietnam_agent_card.name, "vietnam-farm-agent-1"),
  COLOMBIA_FARM_AGENT_URL: (colombia_agent_card.name, "colombia-farm-agent"),
}
# helper function to get farm URL by card name
def get_farm_url_by_card_name(card_name):
  for url, (name, _) in CARD_URL_MAP.items():
    if name == card_name:
      return url
  return None

class IdentityServiceOSSImpl(IdentityService):
  """
  Implementation of the IdentityService interface for managing identity-related operations
  such as badge creation, verification, and issuer registration.
  """

  def __init__(self, idp_url=None, hydra_admin_url=None, agent_url=None, retries=7, sleep_interval=2, identity_api_url=None):
    """
    Initialize the IdentityServiceOSSImpl instance.

    Args:
        idp_url (str): Identity Provider URL (e.g., ngrok URL).
        hydra_admin_url (str): Hydra Admin URL for OAuth client management.
        agent_url (str): URL of the agent.
        retries (int): Number of retries for command execution.
        sleep_interval (int): Interval between retries in seconds.
        identity_api_url (str): Optional Identity API URL.
    """
    self._idp_url = idp_url
    self._hydra_admin_url = hydra_admin_url
    self.agent_url = agent_url
    self.retries = retries
    self.sleep_interval = sleep_interval
    self.identity_api_url = identity_api_url or os.getenv("IDENTITY_API_SERVER_URL")

  def get_all_apps(self) -> IdentityServiceApps:
    """
    Retrieve all registered applications.

    Returns:
        IdentityServiceApps: A list of registered applications.

    Raises:
        RuntimeError: If an error occurs while retrieving applications.
    """
    try:
      apps = IdentityServiceApps(apps=[
        IdentityServiceApp(
          id=CARD_URL_MAP.get(self.agent_url)[1],
          name=CARD_URL_MAP.get(self.agent_url)[0],
          type="A2A",
        )
      ])
      return apps
    except KeyError as e:
      logger.error(f"Key error while accessing farm_client_id_map: {e}")
      raise RuntimeError("Failed to retrieve applications due to a key error.") from e
    except Exception as e:
      logger.error(f"Unexpected error while getting all apps: {e}")
      raise RuntimeError("Failed to retrieve all applications.") from e

  def verify_badges(self, badge: Badge) -> Dict[str, Any]:
    """
    Verify the validity of a badge.

    Args:
        badge (Badge): The badge to verify.

    Returns:
        Dict[str, Any]: A dictionary containing the verification status and additional details.

    Raises:
        ValueError: If the badge verification fails or required environment variables are missing.
        RuntimeError: If an unexpected error occurs during verification.
    """
    grpc_server_url = os.getenv("IDENTITY_NODE_GRPC_SERVER_URL", "identity-node:4001")
    logger.info(f"Using identity node gRPC server URL: {grpc_server_url}")
    if not grpc_server_url:
      logger.error("IDENTITY_NODE_GRPC_SERVER_URL is not set.")
      raise ValueError("IDENTITY_NODE_GRPC_SERVER_URL is not set. Cannot verify badge.")

    try:
      identity_sdk = IdentitySdk()
      verified = identity_sdk.verify_badge(badge)

      if not verified:
        return {
          "status": False,
        }

      return {
        "status": True,
      }
    except Exception as e:
      logger.error(f"Error during badge verification: {e}")
      return {
        "status": "error",
        "message": f"An error occurred during badge verification: {str(e)}",
      }

  def get_badge_for_app(self, app_id: str) -> Badge:
    """
    Retrieve a badge for a specific application.

    Args:
        app_id (str): The application ID.

    Returns:
        Badge: The retrieved badge.

    Raises:
        ValueError: If required environment variables are missing or badge retrieval fails.
        RuntimeError: If an unexpected error occurs during badge retrieval.
    """
    grpc_server_url = os.getenv("IDENTITY_NODE_GRPC_SERVER_URL", "identity-node:4001")
    logger.info(f"Using identity node gRPC server URL: {grpc_server_url}")
    if not grpc_server_url:
      logger.error("IDENTITY_NODE_GRPC_SERVER_URL is not set.")
      raise ValueError("IDENTITY_NODE_GRPC_SERVER_URL is not set. Cannot retrieve badge ID.")

    try:
      badge_id = "IDP-" + app_id
      identity_sdk = IdentitySdk()
      badge = identity_sdk.get_badge(badge_id)
      logger.debug(f"Retrieved badge for app {app_id}")
      return badge
    except KeyError as e:
      logger.error(f"Badge ID not found for app {app_id}: {e}")
      raise ValueError(f"Badge ID for app {app_id} is not set.") from e
    except Exception as e:
      logger.error(f"Error retrieving badge for app {app_id}: {e}")
      raise RuntimeError("Failed to retrieve badge.") from e

  async def create_badge(self, agent_url: str, api_key: str):
    """
    Create a badge for an agent.

    Args:
        agent_url (str): The agent's URL.
        api_key (str): API key for authentication.

    Raises:
        ValueError: If required parameters are missing.
        RuntimeError: If badge creation fails.
    """
    if not agent_url:
      logger.error("Agent URL is not set.")
      raise ValueError("Agent URL is not set. Cannot create badge.")

    logger.info(f"Hydra Admin URL: {self._hydra_admin_url}, Agent URL: {agent_url}")

    try:
      hydra_service = HydraClientServiceImpl(self._hydra_admin_url)

      client_id = CARD_URL_MAP.get(self.agent_url)[1]
      client_secret = "secret-test"

      hydra_service.create_oauth_client(client_id, client_secret)

      self.client_id = client_id
      self.client_secret = client_secret
      await self.generate_metadata()
      await self.issue_badge()
      await self.publish_badge()
      logger.info("Badge published for client ID: %s", client_id)

    except KeyError as e:
      logger.error(f"Key error during badge creation: {e}")
      raise ValueError("Failed to map client ID.") from e
    except Exception as e:
      logger.error(f"Error while creating badge: {e}")
      raise RuntimeError("Failed to create badge.") from e

  async def _run_command(self, command, expected_output=None, output_validation=None):
    """
    Run a shell command asynchronously with retries and optional output validation.

    Args:
        command (str): The shell command to execute.
        expected_output (str): Expected output string to validate.
        output_validation (callable): Optional validation function for the output.

    Raises:
        RuntimeError: If the command fails after all retries.
    """
    for attempt in range(self.retries):
      try:
        process = await asyncio.create_subprocess_shell(
          command,
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
          output = stdout.decode().strip()
          logger.debug(output)

          if expected_output and expected_output not in output:
            logger.warning("Expected output not found in command output.")
          if output_validation and not output_validation(output):
            logger.warning("Output validation failed.")
          return
        else:
          raise RuntimeError(stderr.decode().strip())
      except Exception as e:
        logger.warning(f"Attempt {attempt + 1} failed: {e}")
        if attempt < self.retries - 1:
          await asyncio.sleep(self.sleep_interval)
        else:
          logger.error("Max retries reached. Command failed.")
          raise RuntimeError(f"Command failed after {self.retries} attempts.") from e

  async def connect_vault(self):
    """
    Connect to the identity vault.
    """
    command = 'identity vault connect file -f ./vault.json -v "My Vault"'
    await self._run_command(command)

  async def generate_vault_key(self):
    """
    Generate a new key in the identity vault.
    """
    command = 'identity vault key generate'
    await self._run_command(command)

  async def register_issuer(self, client_id, client_secret):
    """
    Register an issuer with the Identity Provider.

    Args:
        client_id (str): OAuth client ID.
        client_secret (str): OAuth client secret.
    """
    command = (
      f'printf "\\n\\n" | identity issuer register -o "Acorda Test" '
      f'-c "{client_id}" -s "{client_secret}" '
      f'-u "{self._idp_url}"'
    )
    if self.identity_api_url:
      command += f' -i "{self.identity_api_url}"'
    expected_output = "Successfully registered as an Issuer with:"
    await self._run_command(command, expected_output, self._validate_register_issuer_output)

  async def generate_metadata(self):
    """
    Generate metadata for the issuer.
    """
    logger.info(f"INFO: {self.client_id}, {self.client_secret}, {self._idp_url}")

    command = (
      f'identity metadata generate -c "{self.client_id}" -s "{self.client_secret}" '
      f'-u "{self._idp_url}"'
    )
    if self.identity_api_url:
      command += f' -i "{self.identity_api_url}"'

    logger.info(f"Generating metadata with command: {command}")
    expected_output = "Generated metadata with ID:"
    await self._run_command(command, expected_output, self._validate_metadata_generate_output)

  async def issue_badge(self):
    """
    Issue a badge for the agent.
    """
    command = f'identity badge issue a2a -u {self.agent_url}'
    expected_output = "Issued badge with ID:"
    await self._run_command(command, expected_output, self._validate_issue_badge_output)

  async def publish_badge(self):
    """
    Publish the issued badge.
    """
    logger.info(f"INFO: {self.client_id}, {self.client_secret}, {self._idp_url}")
    command = 'printf "\\n" | identity badge publish'
    if self.identity_api_url:
      command += f' -i "{self.identity_api_url}"'
    logger.info(f"Publishing badge with command: {command}")
    expected_output = "Published the badge"
    await self._run_command(command, expected_output, self._validate_publish_badge_output)

  @staticmethod
  def _validate_register_issuer_output(output):
    """
    Validate the output of the register issuer command.
    """
    return "Successfully registered as an Issuer" in output

  @staticmethod
  def _validate_metadata_generate_output(output):
    """
    Validate the output of the metadata generation command.
    """
    return "Generated metadata" in output

  @staticmethod
  def _validate_issue_badge_output(output):
    """
    Validate the output of the badge issuance command.
    """
    return "Issued badge" in output

  @staticmethod
  def _validate_publish_badge_output(output):
    """
    Validate the output of the badge publishing command.
    """
    return "Published the badge" in output
