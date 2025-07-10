# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os
from dotenv import load_dotenv

load_dotenv()  # Automatically loads from `.env` or `.env.local`

DEFAULT_MESSAGE_TRANSPORT = os.getenv("DEFAULT_MESSAGE_TRANSPORT", "SLIM")
TRANSPORT_SERVER_ENDPOINT = os.getenv("TRANSPORT_SERVER_ENDPOINT", "http://localhost:46357")

FARM_BROADCAST_TOPIC = os.getenv("FARM_BROADCAST_TOPIC", "farm_broadcast")

WEATHER_MCP_SERVER_URL = os.getenv("WEATHER_MCP_SERVER_URL", "http://localhost:8123")

LLM_PROVIDER = os.getenv("LLM_PROVIDER")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()
