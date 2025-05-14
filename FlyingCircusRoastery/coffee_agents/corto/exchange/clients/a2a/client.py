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

import httpx
from uuid import uuid4
from typing import Any
from a2a.client import A2AClient
from a2a.types import SendMessageResponse

AGENT_URL = 'http://localhost:9999'

async def send_message(message: str) -> SendMessageResponse:
  payload: dict[str, Any] = {
    'message': {
      'role': 'user',
      'parts': [{'type': 'text', 'text': message}],
      'messageId': uuid4().hex,
    },
  }

  client = await A2AClient.get_client_from_agent_card_url(
    httpx.AsyncClient(), AGENT_URL
  )

  return await client.send_message(payload=payload)

