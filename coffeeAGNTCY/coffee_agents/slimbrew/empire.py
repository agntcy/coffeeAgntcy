import asyncio
import datetime
import json

from slim_bindings import (
    PyName,
    PySessionConfiguration,
    PySessionDirection,
)

from common import create_slim_app

secret = "secret"

async def create_group_session(moderator_app, channel):
    """
    Creates a group session with the given channel and invites the specified participants.
    """
    session_info = await moderator_app.create_session(
        PySessionConfiguration.Streaming(
            PySessionDirection.BIDIRECTIONAL,
            topic=channel,
            moderator=True,
            max_retries=20,
            timeout=datetime.timedelta(seconds=60),
            mls_enabled=True,
        ))
    return session_info

async def groupchat_moderator(secret: str, channel: PyName, invitees: list[PyName]) -> tuple[list[str], Exception]:
    local_name = PyName("agntcy", "slimbrew", "moderator")
    moderator_slim_app = await create_slim_app(secret, local_name)
    async with moderator_slim_app:
        # create session
        session_info = await create_group_session(moderator_slim_app, channel)

        # invite participants
        for invitee in invitees:
            print(f"Inviting {invitee}")
            await moderator_slim_app.set_route(invitee)
            await moderator_slim_app.invite(session_info, invitee)

        await asyncio.sleep(2)

        # publish message
        print(f"Publishing message to {channel}")

        # TODO: provide more session metadata so we dont have to rely on application-level message sematics
        message = {
            "text": "Hello everyone!",
            "respond_to_source": False,
            "respond_to_group": True,
            "random_group_message_backoff": 6
        }

        await moderator_slim_app.publish(session_info, json.dumps(message).encode(), channel)

        while True:
            _, msg = await moderator_slim_app.receive(session=session_info.id)
            print(f"Received message in session {session_info.id}: {msg.decode()}")

async def broadcast_moderator(secret: str, channel: PyName, invitees: list[PyName]) -> tuple[list[str], Exception]:
    local_name = PyName("agntcy", "slimbrew", "moderator")
    moderator_slim_app = await create_slim_app(secret, local_name)
    async with moderator_slim_app:
        # create session
        session_info = await create_group_session(moderator_slim_app, channel)

        # invite participants
        for invitee in invitees:
            print(f"Inviting {invitee}")
            await moderator_slim_app.set_route(invitee)
            await moderator_slim_app.invite(session_info, invitee)

        await asyncio.sleep(2)

        # publish message
        print(f"Publishing message to {channel}")

        message = {
            "text": "Hello from moderator!",
            "respond_to_source": True,
        }

        await moderator_slim_app.publish(session_info, json.dumps(message).encode(), channel)

        while True:
            _, msg = await moderator_slim_app.receive(session=session_info.id)
            print(f"Received message in session {session_info.id}: {msg.decode()}")

async def unique_topic_pubsub(shared_channel):
    """
    When each member has its own topic, pub-sub works but is confusing
    because the moderator publishes to a shared channel while participants
    listen on their unique topics.
    """
    invitees = [PyName("agntcy", "namespace1", "coruscant-farm"), PyName("agntcy", "namespace1", "tatooine-farm")]
    await broadcast_moderator(secret, shared_channel, invitees)

async def shared_topic_pubsub(shared_channel):
    """
    When multiple members share the same org/namespace/topic, we get slim errors. 
    A slight workaround is to have each participant in a different namespace but the same topic.
    Conceptually this makes more sense but requires namespacing.
    """
    invitees = [PyName("agntcy", "namespace1", "farms"), PyName("agntcy", "namespace2", "farms")]
    await broadcast_moderator(secret, shared_channel, invitees)

async def groupchat(shared_channel):
    """
    This is the same as unique_topic_pubsub but signals to participants they can
    respond to the group channel not directly back to source.
    """
    invitees = [PyName("agntcy", "namespace1", "coruscant-farm"), PyName("agntcy", "namespace1", "tatooine-farm")]
    await groupchat_moderator(secret, shared_channel, invitees)

if __name__ == "__main__":
    shared_channel = PyName("agntcy", "namespace", "group_channel")
    print(dir(shared_channel))
    print(shared_channel.components())
    print(shared_channel.components_strings())


    asyncio.run(unique_topic_pubsub(shared_channel))
    #asyncio.run(shared_topic_pubsub(shared_channel))
    #asyncio.run(groupchat(shared_channel))