import requests
import asyncio

from services.identity_service import IdentityService

CLI_MAX_RETRIES = 3
CLI_RETRY_DELAY = 2

class IdentityServiceImpl(IdentityService):
  def __init__(self, api_key: str, base_url: str):
    self.api_key = api_key
    self.base_url = base_url

  def get_all_apps(self):
    """Fetch all apps."""
    url = f"{self.base_url}/v1alpha1/apps"
    headers = {
      "x-id-api-key": self.api_key,
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      return response.json()
    else:
      raise RuntimeError(f"Failed to fetch apps: {response.status_code}, {response.text}")

  def get_badge_for_app(self, app_id: str):
    """Fetch the current badge issued for the specified app and return the proofValue."""
    url = f"{self.base_url}/v1alpha1/apps/{app_id}/badge"
    headers = {
      "x-id-api-key": self.api_key,
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      badge = response.json()
      proof_value = badge.get("verifiableCredential", {}).get("proof", {}).get("proofValue")
      if proof_value:
        return proof_value
      else:
        raise RuntimeError(f"No proofValue found in the badge for app {app_id}.")
    else:
      raise RuntimeError(f"Failed to fetch badge for app {app_id}: {response.status_code}, {response.text}")

  def verify_badges(self, badge: str):
    """Verify the provided badge data."""
    url = f"{self.base_url}/v1alpha1/badges/verify"
    headers = {
      "Content-Type": "application/json",
      "x-id-api-key": self.api_key,
    }
    data = {"badge": badge}

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
      return response.json()
    else:
      raise RuntimeError(f"Failed to verify badge: {response.status_code}, {response.text}")

  ## TODO: This is a temporary implementation that uses the identity-cli binary. When the API or SDK is available, this should be replaced.
  async def create_badge(self, agent_url: str, svc_api_key: str):
    """Create a badge using the identity-cli binary with the --key flag asynchronously."""
    command = ["identity-cli", "badge", "create", "--key", svc_api_key, agent_url]

    for attempt in range(1, CLI_MAX_RETRIES + 1):
      try:
        # Use asyncio to run the command asynchronously
        process = await asyncio.create_subprocess_exec(
          *command,
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
          return stdout.decode().strip()
        else:
          print(f"Attempt {attempt} failed with return code: {process.returncode}")
          print("Standard Output:", stdout.decode().strip())
          print("Standard Error:", stderr.decode().strip())
          if attempt == CLI_MAX_RETRIES:
            raise RuntimeError(f"Failed to create badge after {CLI_MAX_RETRIES} attempts. See logs for details.")
      except Exception as e:
        print(f"Attempt {attempt} encountered an unexpected error: {e}")
        if attempt == CLI_MAX_RETRIES:
          raise RuntimeError("An unexpected error occurred. See logs for details.")

      print(f"Retrying in {CLI_RETRY_DELAY} seconds...")
      await asyncio.sleep(CLI_RETRY_DELAY)