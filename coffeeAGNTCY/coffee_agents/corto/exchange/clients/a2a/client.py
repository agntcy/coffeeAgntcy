from typing import Any
from uuid import uuid4

from httpx import AsyncClient, Timeout

from a2a.client import A2AClient
from a2a.types import SendMessageRequest, MessageSendParams, Message, Part, TextPart, Role
from config.config import FARM_AGENT_HOST, FARM_AGENT_PORT


AGENT_URL = f"http://{FARM_AGENT_HOST}:{FARM_AGENT_PORT}"

async def send_message(input_payload: dict):
  """ Sends a message to the agent server and returns the response. """
  print(f"Sending message to {AGENT_URL} with payload: {input_payload}")

  client = await A2AClient.get_client_from_agent_card_url(
    AsyncClient(timeout=Timeout(15.0)), AGENT_URL
  )

  request = SendMessageRequest(
      params=MessageSendParams(
          skill_id="estimate_flavor",
          sender_id="coffee-exchange-agent",
          receiver_id="flavor-profile-farm-agent",
          message=Message(
            messageId=str(uuid4()),
            role=Role.user,
            parts=[Part(TextPart(text=input_payload["prompt"]))],
        )
      )
  )

  response = await client.send_message(request.params)
  if response.root.result:
    if not response.root.result.parts:
      raise ValueError("No response parts found in the message.")
    part = response.root.result.parts[0].root
    if hasattr(part, "text"):
      return part.text
  elif response.root.error:
    raise Exception(f"A2A error: {response.error.message}")


  raise Exception("Unknown response type")
  
  
