# Copyright 2025 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import os
from dotenv import load_dotenv

load_dotenv()  # Automatically loads from `.env` or `.env.local`

# --- Lungo ---
#DEFAULT_MESSAGE_TRANSPORT = os.getenv("DEFAULT_MESSAGE_TRANSPORT", "NATS")
#TRANSPORT_SERVER_ENDPOINT = os.getenv("TRANSPORT_SERVER_ENDPOINT", "localhost:4222")

DEFAULT_MESSAGE_TRANSPORT = os.getenv("DEFAULT_MESSAGE_TRANSPORT", "SLIM")
TRANSPORT_SERVER_ENDPOINT = os.getenv("TRANSPORT_SERVER_ENDPOINT", "http://localhost:46357")

FARM_BROADCAST_TOPIC = os.getenv("FARM_BROADCAST_TOPIC", "farm_broadcast")

WEATHER_MCP_SERVER_URL = os.getenv("WEATHER_MCP_SERVER_URL", "http://localhost:8123")

LLM_PROVIDER = os.getenv("LLM_PROVIDER")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()
