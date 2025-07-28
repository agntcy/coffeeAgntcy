# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os
from dotenv import load_dotenv

load_dotenv()  # Automatically loads from `.env` or `.env.local`

DEFAULT_MESSAGE_TRANSPORT = os.getenv("DEFAULT_MESSAGE_TRANSPORT", "SLIM")
TRANSPORT_SERVER_ENDPOINT = os.getenv("TRANSPORT_SERVER_ENDPOINT", "http://localhost:46357")

FARM_BROADCAST_TOPIC = os.getenv("FARM_BROADCAST_TOPIC", "farm_broadcast")

WEATHER_MCP_SERVER_URL = os.getenv("WEATHER_MCP_SERVER_URL", "http://localhost:8125")

LLM_PROVIDER = os.getenv("LLM_PROVIDER")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()

ENABLE_HTTP = os.getenv("ENABLE_HTTP", "true").lower() in ("true", "1", "yes")

# AGNTCY Identity Integration
## These API Keys are created in OSS environment and hardcoded for demo purposes.
IDENTITY_VIETNAM_AGENT_SERVICE_API_KEY = os.getenv("IDENTITY_VIETNAM_AGENT_SERVICE_API_KEY", "80arL5Rpvy3IL14IYEo2;<wq9)2>Z!!r-:(40eUTX+E5NAp)(g)2b2@u;qS2S2z{")
IDENTITY_COLOMBIA_AGENT_SERVICE_API_KEY = os.getenv("IDENTITY_COLOMBIA_AGENT_SERVICE_API_KEY", "D4tPQ>S+if24h5xX9y+@U1{PiZ6e-nmK0eG4h@5@@7,r<J-I:H5bjf9!-Z@59Z2J")
IDENTITY_API_KEY = os.getenv("IDENTITY_API_KEY", "n-;bYO5iMtdP7X787PP5G63E6e9O-6,U2paS@y+>-zv15Y[7{![l@@eg(8chS;LU")
## Endpoint to access Identity API. Refer to https://identity-docs.staging.outshift.ai/docs/api
IDENTITY_API_SERVER_URL = os.getenv("IDENTITY_API_SERVER_URL", "https://api.identity-service.staging.outshift.ai")
## URLs for the farm agents' well-known agent cards
VIETNAM_FARM_AGENT_URL = os.getenv("VIETNAM_FARM_AGENT_URL", "http://127.0.0.1:9997/.well-known/agent.json")
COLOMBIA_FARM_AGENT_URL = os.getenv("COLOMBIA_FARM_AGENT_URL", "http://127.0.0.1:9998/.well-known/agent.json")
