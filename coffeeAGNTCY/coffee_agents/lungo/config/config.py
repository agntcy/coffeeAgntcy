# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os
from dotenv import load_dotenv

load_dotenv()  # Automatically loads from `.env` or `.env.local`

DEFAULT_MESSAGE_TRANSPORT = os.getenv("DEFAULT_MESSAGE_TRANSPORT", "NATS")
TRANSPORT_SERVER_ENDPOINT = os.getenv("TRANSPORT_SERVER_ENDPOINT", "nats://localhost:4222")

FARM_BROADCAST_TOPIC = os.getenv("FARM_BROADCAST_TOPIC", "farm_broadcast")
GROUP_CHAT_TOPIC = os.getenv("GROUP_CHAT_TOPIC", "group_chat")

LLM_PROVIDER = os.getenv("LLM_PROVIDER")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()

ENABLE_HTTP = os.getenv("ENABLE_HTTP", "true").lower() in ("true", "1", "yes")

# AGNTCY Identity Integration
## These API Keys are created in OSS environment and hardcoded for demo purposes.
IDENTITY_VIETNAM_AGENT_SERVICE_API_KEY = os.getenv("IDENTITY_VIETNAM_AGENT_SERVICE_API_KEY", ';46pkNq5([J2<[{40b;d0Jg74IRATpaUeW1Bi1}@@ILUFcqo3U4;(p31)+m)p!2Y')
IDENTITY_COLOMBIA_AGENT_SERVICE_API_KEY = os.getenv("IDENTITY_COLOMBIA_AGENT_SERVICE_API_KEY", ")300n,J:bk<6H+[Awo0zMH]()!<8+Z5wTGTtR{d88bT@c<9cTzc:E65DRx512K2l")
IDENTITY_API_KEY = os.getenv("IDENTITY_API_KEY", "3]U;sp6>p@7:Vl7XN8<-2i2+w@;7HMN,g0ZgVGb3d<n3)34]3;+k3hR4OAfiGLQk")
## Endpoint to access Identity API. Refer to https://identity-docs.staging.outshift.ai/docs/api
IDENTITY_API_SERVER_URL = os.getenv("IDENTITY_API_SERVER_URL", "https://api.agent-identity.outshift.com")
## URLs for the farm agents' well-known agent cards
VIETNAM_FARM_AGENT_URL = os.getenv("VIETNAM_FARM_AGENT_URL", "http://127.0.0.1:9997/.well-known/agent-card.json")
COLOMBIA_FARM_AGENT_URL = os.getenv("COLOMBIA_FARM_AGENT_URL", "http://127.0.0.1:9998/.well-known/agent-card.json")

