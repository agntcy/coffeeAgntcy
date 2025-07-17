# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import subprocess
import time
import logging

from exchange.service.identity_service import IdentityService

logger = logging.getLogger("lungo.supervisor.identity_service")

class IdentityServiceImpl(IdentityService):
  """Implementation of the IdentityService interface."""

  def __init__(self, idp_url, client_id, client_secret, farm_agent_url, retries=7, sleep_interval=2, identity_api_url=None):
    self._idp_url = idp_url  # Private attribute, cannot be modified externally after initialization
    self.client_id = client_id
    self.client_secret = client_secret
    self.farm_agent_url = farm_agent_url
    self.retries = retries
    self.sleep_interval = sleep_interval
    self.identity_api_url = identity_api_url  # Optional parameter


  def _run_command(self, command, expected_output=None, output_validation=None):
    """Run a shell command with retries and optional output validation."""
    for attempt in range(self.retries):
      try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        logger.debug(result.stdout)

        # Validate output if expected_output or validation function is provided
        if expected_output and expected_output not in result.stdout:
          logger.debug(f"Warning: Expected output not found in command output.")
        if output_validation and not output_validation(result.stdout):
          logger.debug(f"Warning: Output validation failed.")
        return  # Exit the function if the command succeeds
      except subprocess.CalledProcessError as e:
        logger.debug(f"Attempt {attempt + 1} failed: {e.stderr}")
        if attempt < self.retries - 1:
          time.sleep(self.sleep_interval)  # Wait before retrying
        else:
          logger.debug("Max retries reached. Command failed.")
          raise Exception(f"Command failed after {self.retries} attempts: {e.stderr}")

  def connect_vault(self):
    command = 'identity vault connect file -f ~/.identity/vault.json -v "My Vault"'
    self._run_command(command)

  def generate_vault_key(self):
    command = 'identity vault key generate'
    self._run_command(command)

  def register_issuer(self):
    command = (
      f'printf "\\n\\n" | identity issuer register -o "Acorda Test" '
      f'-c "{self.client_id}" -s "{self.client_secret}" '
      f'-u "{self._idp_url}"'
    )
    if self.identity_api_url:
      command += f' -i "{self.identity_api_url}"'
    expected_output = "Successfully registered as an Issuer with:"
    self._run_command(command, expected_output, self._validate_register_issuer_output)

  def generate_metadata(self):
    command = (
      f'identity metadata generate -c "{self.client_id}" -s "{self.client_secret}" '
      f'-u "{self._idp_url}"'
    )
    expected_output = "Generated metadata with ID:"
    self._run_command(command, expected_output, self._validate_metadata_generate_output)

  def issue_badge(self):
    command = f'identity badge issue a2a -u {self.farm_agent_url}/.well-known/agent.json'
    expected_output = "Issued badge with ID:"
    self._run_command(command, expected_output, self._validate_issue_badge_output)

  def publish_badge(self):
    command = 'printf "\\n" | identity badge publish'
    expected_output = "Published the badge"
    self._run_command(command, expected_output, self._validate_publish_badge_output)

  @staticmethod
  def _validate_register_issuer_output(output):
    return "Successfully registered as an Issuer" in output

  @staticmethod
  def _validate_metadata_generate_output(output):
    return "Generated metadata" in output

  @staticmethod
  def _validate_issue_badge_output(output):
    return "Issued badge" in output

  @staticmethod
  def _validate_publish_badge_output(output):
    return "Published the badge" in output
