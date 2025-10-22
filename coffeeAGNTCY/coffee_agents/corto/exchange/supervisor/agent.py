# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from uuid import uuid4
from ioa_observe.sdk.decorators import agent, graph
from exchange.supervisor.shared import get_factory
from agntcy_app_sdk.protocols.a2a.protocol import A2AProtocol
from config.config import DEFAULT_MESSAGE_TRANSPORT, TRANSPORT_SERVER_ENDPOINT

from a2a.types import (
    AgentCard,
    SendMessageRequest,
    MessageSendParams,
    Message,
    Part,
    TextPart,
    Role,
)


from farm.card import AGENT_CARD as farm_agent_card

logger = logging.getLogger("corto.supervisor.agent")


@agent(name="exchange_agent")
class ExchangeAgent:
    @staticmethod
    async def a2a_client_send_message(prompt: str):
        """
        Send the user-provided prompt to the farm agent over A2A transport and
        return the resulting response payload.

        Args:
            prompt (str): Plain-text prompt to forward to the farm agent.

        Returns:
            Any: Whatever payload is returned by `client.send_message`.

        Raises:
            Exception: Propagated when transport or message handling fails.
        """
        try:
            factory = get_factory()
            a2a_topic = A2AProtocol.create_agent_topic(farm_agent_card)
            transport = factory.create_transport(
                DEFAULT_MESSAGE_TRANSPORT,
                endpoint=TRANSPORT_SERVER_ENDPOINT,
                # SLIM transport requires a routable name (org/namespace/agent) to build the PyName used for request-reply routing
                name="default/default/exchange"
            )
            client = await factory.create_client(
                "A2A",
                agent_topic=a2a_topic,
                transport=transport)

            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(
                    message=Message(
                        message_id=str(uuid4()),
                        role=Role.user,
                        parts=[Part(TextPart(text=prompt))],
                    )
                )
            )

            # Send and validate response
            response = await client.send_message(request)
            logger.info(f"Response received from A2A agent: {response}")
            if response.root.result:
                if not response.root.result.parts:
                    raise ValueError("No response parts found in the message.")
                part = response.root.result.parts[0].root
                if hasattr(part, "text"):
                    return part.text
            elif response.root.error:
                raise Exception(f"A2A error: {response.error.message}")

        except Exception as e:
            logger.error(f"Error in serve method: {e}")
            raise Exception(str(e))
