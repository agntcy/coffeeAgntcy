import asyncio
import json
import random

from slim_bindings import PyName
from common import create_slim_app

secret = "secret"

async def subscribe(org, namespace, topic):
    """
    Key challenges: 
    Multiple participants cant subscribe to the name PyName, one of the tuple entries must be unique.
    """
    local_name = PyName(org, namespace, topic)
    slim_app = await create_slim_app(secret, local_name)
    async with slim_app:
        recv_session, data = await slim_app.receive()

        while True:
            recv_session, msg_rcv = await slim_app.receive(
                session=recv_session.id
            )

            msg = json.loads(msg_rcv.decode())
            print(f"Received message in session {recv_session.id}: {msg}")

            if msg.get("respond_to_source", True):
                # reply to the sender
                print(f"sending reply back to sender {recv_session.destination_name}")
                print(recv_session.destination_name.id)

                print(recv_session.destination_name.components())
                '''parts = recv_session.destination_name.split("/")
                org, namespace, topic = parts[0], parts[1], parts[2]

                print(f"Parsed destination name into org: {org}, namespace: {namespace}, topic: {topic}")'''

                await slim_app.publish_to(
                    recv_session, f"Hello from {namespace}/{topic}".encode()
                )
            elif msg.get("respond_to_group", True):
                # reply to the group
                backoff = msg.get("random_group_message_backoff", 0)
                if backoff > 0:
                    await asyncio.sleep(random.uniform(0, backoff))

                print(f"sending reply back to group")
                message = {
                    "text": f"Hello from {namespace}/{topic}",
                    "respond_to_source": False,
                    "respond_to_group": True,
                    "random_group_message_backoff": backoff
                }
                
                await slim_app.publish(
                    recv_session,
                    json.dumps(message).encode(),
                    recv_session.destination_name,
                )
            else:
                print(f"No response sent for message: {msg}")

async def unique_topic_test(topic="coruscant-farm"):
    await subscribe("agntcy", "namespace1", topic)

async def shared_topic_test(topic="farms"):
    await subscribe("agntcy", "namespace1", topic)
        
if __name__ == "__main__":
    asyncio.run(unique_topic_test())
    #asyncio.run(shared_topic_test())