# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

## Note: please do not modify this script.

import uuid
import logging
import asyncio
from services.hydra_client_service_impl import HydraClientServiceImpl
from services.identity_service_oss_impl import IdentityServiceOSSImpl
from config.config import HYDRA_ADMIN_URL

async def register_issuer(hydra_admin_url, idp_url, identity_api_url=None):
    """
    Execute only the first iteration of the initialize_clients_and_issue_badges function.
    """
    try:
        hydra_service = HydraClientServiceImpl(hydra_admin_url)

        client_id = f"client-{uuid.uuid4().hex[:5]}"
        client_secret = f"secret-{uuid.uuid4().hex[:5]}"
        # Create OAuth client
        _ = hydra_service.create_oauth_client(client_id, client_secret)

        # Initialize and process badge workflow
        identity_service = IdentityServiceOSSImpl(
            idp_url=idp_url,
            identity_api_url=identity_api_url
        )

        # Connect to vault and register issuer if required
        await identity_service.connect_vault()
        await identity_service.generate_vault_key()
        await identity_service.register_issuer(client_id, client_secret)

    except Exception as e:
        logging.error(f"Error during first iteration: {e}")

if __name__ == "__main__":
    idp_url = "https://ca6e487f8d55.ngrok-free.app"
    asyncio.run(register_issuer(hydra_admin_url=HYDRA_ADMIN_URL, idp_url=idp_url))
    print("Issuer registration completed.")
