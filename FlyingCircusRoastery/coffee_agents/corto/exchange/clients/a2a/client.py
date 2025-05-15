from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2AClient
from a2a.types import SendMessageResponse


AGENT_URL = 'http://localhost:9999'


async def send_message(message: str) -> SendMessageResponse:
  """ Sends a message to the agent server and returns the response. """
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

