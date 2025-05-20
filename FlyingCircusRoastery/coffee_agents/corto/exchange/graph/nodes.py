from a2a.types import (
    AgentCard, 
    SendMessageRequest, 
    MessageSendParams, 
    Message, 
    Part, 
    TextPart, 
    Role,
)
from uuid import uuid4
from gateway_sdk.factory import GatewayFactory
from gateway_sdk.protocols.a2a.gateway import A2AProtocol
from config.config import AGP_GATEWAY_URL, DEFAULT_MESSAGE_TRANSPORT

class FarmContact:
    """ 
    A2A client for the Remote Coffee Farm Agent. 
    """
    def __init__(self, remote_agent_card: AgentCard):
        self.remote_agent_card = remote_agent_card
        self._a2a_topic = A2AProtocol.create_agent_topic(self.remote_agent_card)
        
        self._factory = GatewayFactory()
        self._transport = self._factory.create_transport(DEFAULT_MESSAGE_TRANSPORT, AGP_GATEWAY_URL)
        self._a2a_client = None
    
    def __str__(self):
        return f"FarmContact(remote_farm_name={self.remote_agent_card.name}, remote_farm_version={self.remote_agent_card.version}"
    
    async def invoke(self, state: dict):
        resp = await self.message_farmer(state["input_payload"])
        return {"output": resp}

    async def message_farmer(self, input_payload: dict):
        """ Sends a message to the agent server and returns the response. """
        print(f"Sending message to {self.remote_agent_card.name} with payload: {input_payload}")

        if not self._a2a_client:
            self._a2a_client = await self._factory.create_client("A2A", agent_topic=self._a2a_topic, transport=self._transport)

        request = SendMessageRequest(
            params=MessageSendParams(
                skill_id="estimate_flavor",
                sender_id="coffee-exchange-agent",
                receiver_id="flavor-profile-farm-agent",
                message=Message(
                    messageId=str(uuid4()),
                    role=Role.user,
                    parts=[Part(TextPart(text="Estimate coffee flavor"))],
                    metadata = input_payload
                )
            )
        )
            
        response = await self._a2a_client.send_message(request.params)
        if response.root.result:
            if not response.root.result.parts:
                raise ValueError("No response parts found in the message.")
            part = response.root.result.parts[0].root
            if hasattr(part, "text"):
                return part.text
        elif response.root.error:
            raise Exception(f"A2A error: {response.error.message}")

        raise Exception("Unknown response type")
    
