# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MESSAGE_TRANSPORT = os.getenv("DEFAULT_MESSAGE_TRANSPORT", "SLIM")
TRANSPORT_SERVER_ENDPOINT = os.getenv(
    "TRANSPORT_SERVER_ENDPOINT", "http://localhost:46357"
)
SLIM_SERVER = os.getenv("SLIM_SERVER", "localhost:46357")
NATS_SERVER = os.getenv("NATS_SERVER", "localhost:4222")

# Deadline (seconds) for a single SLIM request/reply exchange. The app SDK defaults
# to 6s, which expires before an LLM-backed agent can answer.
SLIM_REQUEST_TIMEOUT_SECONDS = int(os.getenv("SLIM_REQUEST_TIMEOUT_SECONDS", "20"))

# When true, the A2A servers may start their SLIM interfaces with the app SDK's
# public placeholder secret if SLIM_SHARED_SECRET is unset or is the placeholder.
# Local demos only: without it the SDK refuses to start those interfaces.
SLIM_ALLOW_PLACEHOLDER_SECRET = os.getenv(
    "SLIM_ALLOW_PLACEHOLDER_SECRET", "false"
).strip().lower() in (
    "true",
    "1",
    "yes",
)

FARM_AGENT_HOST = os.getenv("FARM_AGENT_HOST", "localhost")
FARM_AGENT_PORT = int(os.getenv("FARM_AGENT_PORT", "9999"))

LLM_MODEL = os.getenv("LLM_MODEL", "")
OAUTH2_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID", "")
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET", "")
OAUTH2_TOKEN_URL = os.getenv("OAUTH2_TOKEN_URL", "")
OAUTH2_BASE_URL = os.getenv("OAUTH2_BASE_URL", "")
OAUTH2_APPKEY = os.getenv("OAUTH2_APPKEY", "")

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()
