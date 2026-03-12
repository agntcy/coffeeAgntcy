# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os
from dotenv import load_dotenv

load_dotenv()  # Automatically loads from `.env` or `.env.local`

# OTEL_SDK_DISABLED: common var used by 3rd-party libs built on OpenTelemetry (OTEL). When true, tracing is disabled.
_otel_sdk_disabled_raw = os.getenv("OTEL_SDK_DISABLED", "false").strip().lower()
OTEL_SDK_DISABLED = _otel_sdk_disabled_raw in ("true", "1", "yes")
if OTEL_SDK_DISABLED:
    os.environ.pop("OTLP_HTTP_ENDPOINT", None)

SLIM_SERVER = os.getenv("SLIM_SERVER", "localhost:46357")

NATS_SERVER = os.getenv("NATS_SERVER", "localhost:4222")

PREFERRED_A2A_TRANSPORT = os.getenv("PREFERRED_A2A_TRANSPORT", "slimrpc")

# some services may choose to use http for health checking endpoints, but the agents themselves will communicate over A2A (e.g. via SLIM)
ENABLE_HTTP = os.getenv("ENABLE_HTTP", "true").lower() in ("true", "1", "yes")

if os.getenv("SLIM_SHARED_SECRET") is None:
    # set a default value for development/testing
    os.environ["SLIM_SHARED_SECRET"] = "slim-shared-secret-REPLACE_WITH_RANDOM_32PLUS_CHARS"

LLM_MODEL = os.getenv("LLM_MODEL", "")

## Oauth2 OpenAI Provider
OAUTH2_CLIENT_ID= os.getenv("OAUTH2_CLIENT_ID", "")
OAUTH2_CLIENT_SECRET= os.getenv("OAUTH2_CLIENT_SECRET", "")
OAUTH2_TOKEN_URL= os.getenv("OAUTH2_TOKEN_URL", "")
OAUTH2_BASE_URL= os.getenv("OAUTH2_BASE_URL", "")
OAUTH2_APPKEY= os.getenv("OAUTH2_APPKEY", "")

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()

ENSURE_STREAMING_LLM = os.getenv("ENSURE_STREAMING_LLM", "false").strip().lower() in ("true", "1", "yes")
HOT_RELOAD_MODE = os.getenv("HOT_RELOAD_MODE", "false").strip().lower() in ("true", "1", "yes")

# This is for demo purposes only. In production, use secure methods to manage API keys.
IDENTITY_API_KEY = os.getenv("IDENTITY_API_KEY", "487>t:7:Ke5N[kZ[dOmDg2]0RQx))6k}bjARRN+afG3806h(4j6j[}]F5O)f[6PD")
IDENTITY_API_SERVER_URL = os.getenv("IDENTITY_API_SERVER_URL", "https://api.agent-identity.outshift.com")
