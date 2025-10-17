# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os
from dotenv import load_dotenv

load_dotenv()  # Automatically loads from `.env` or `.env.local`

DEFAULT_MESSAGE_TRANSPORT = os.getenv("DEFAULT_MESSAGE_TRANSPORT", "NATS")
TRANSPORT_SERVER_ENDPOINT = os.getenv("TRANSPORT_SERVER_ENDPOINT", "nats://localhost:4222")

FARM_BROADCAST_TOPIC = os.getenv("FARM_BROADCAST_TOPIC", "farm_broadcast")

LLM_PROVIDER = os.getenv("LLM_PROVIDER")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()

ENABLE_HTTP = os.getenv("ENABLE_HTTP", "true").lower() in ("true", "1", "yes")

# AGNTCY Identity Integration
## These API Keys are created in OSS environment and hardcoded for demo purposes.
IDENTITY_VIETNAM_AGENT_SERVICE_API_KEY = os.getenv("IDENTITY_VIETNAM_AGENT_SERVICE_API_KEY", 'T7lR8I446D3,+<gbev21cNAMIWmrB}<4C5@W@38;ur;}{+}8mpJ3pgV<]M-8sT3z')
IDENTITY_COLOMBIA_AGENT_SERVICE_API_KEY = os.getenv("IDENTITY_COLOMBIA_AGENT_SERVICE_API_KEY", "2px6OFF;Z[x!1Z7cXU,)5@0vCivh)TSDoNd7t!]b7!p8}+18B9R60]L0v5c]{By{")
IDENTITY_API_KEY = os.getenv("IDENTITY_API_KEY", "487>t:7:Ke5N[kZ[dOmDg2]0RQx))6k}bjARRN+afG3806h(4j6j[}]F5O)f[6PD")
## Endpoint to access Identity API. Refer to https://identity-docs.staging.outshift.ai/docs/api
IDENTITY_API_SERVER_URL = os.getenv("IDENTITY_API_SERVER_URL", "https://api.agent-identity.outshift.com")
## URLs for the farm agents' well-known agent cards
VIETNAM_FARM_AGENT_URL = os.getenv("VIETNAM_FARM_AGENT_URL", "http://127.0.0.1:9997/.well-known/agent-card.json")
COLOMBIA_FARM_AGENT_URL = os.getenv("COLOMBIA_FARM_AGENT_URL", "http://127.0.0.1:9998/.well-known/agent-card.json")

