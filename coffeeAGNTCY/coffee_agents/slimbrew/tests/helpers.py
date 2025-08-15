import asyncio
import datetime
import time
from typing import Iterable, List


from slim_bindings import (
    Slim,
    PyName,
    PyService,
    PyIdentityProvider,
    PyIdentityVerifier,
    PySessionInfo,
    PySessionConfiguration,
    PySessionDirection,
)

def shared_secret_identity(
    identity: str, secret: str
) -> tuple[PyIdentityProvider, PyIdentityVerifier]:
    """
    Create a provider and verifier using a shared secret.

    :param identity: A unique string, identifier of the app.
    :param secret: A shared secret used for authentication.
    :return: A tuple of (provider, verifier).
    """
    provider: PyIdentityProvider = PyIdentityProvider.SharedSecret(
        identity=identity, shared_secret=secret
    )
    verifier: PyIdentityVerifier = PyIdentityVerifier.SharedSecret(
        identity=identity, shared_secret=secret
    )

    return provider, verifier

async def create_slim_app(slim_endpoint, secret: str, local_name: PyName) -> PyService:
    """
    Create a SLIM app instance with the given shared secret.
    This app will be used to communicate with other SLIM nodes in the network.

    :param secret: A shared secret used for authentication.
    :param local_name: A unique name for the SLIM app instance.
                       It will be used to identify the app in the SLIM network.
    :return: A SLIM app instance.
    """

    # Create the provider and verifier using the shared secret.
    provider, verifier = shared_secret_identity(
        identity=f"{local_name}",
        secret=secret,
    )

    # Create the SLIM app. This is a in-process SLIM client that can be used to
    # exchange messages with other SLIM nodes in the network.
    slim_app = await Slim.new(local_name, provider, verifier)

    # Connect the SLIM app to the SLIM network.
    _ = await slim_app.connect(
        {"endpoint": slim_endpoint, "tls": {"insecure": True}}
    )

    # Return the SLIM app instance.
    return slim_app

async def collect_messages(app: PyService, session_id: PySessionInfo, duration=10.0) -> List[str]:
    """
    Collect messages from the specified session within the given duration.
    """
    messages = []
    deadline = time.time() + duration

    while time.time() < deadline:
        try:
            # Wait for at most 1s per iteration so we can re-check the deadline
            _, msg = await asyncio.wait_for(
                app.receive(session=session_id),
                timeout=1.0
            )
            print(f"Received message from {session_id}: {msg.decode()}")
            messages.append(msg.decode())
        except asyncio.TimeoutError:
            # No message in this 1s slice → loop again until deadline
            continue

    return messages

async def send_messages(reply_messages: Iterable[str], slim_app: PyService, 
                        recv_session: PySessionInfo, reply_to: PyName):
    """
    Send messages to the specified recipient over provided session.
    """
    for text in reply_messages:
        await slim_app.publish(recv_session, text.encode(), reply_to)


async def run_moderator(slim_endpoint, shared_secret: str, topic_name: str, moderator_name: str, invitees: List[PyName]) -> List[str]:
    # init slim client
    moderator_slim_app = await create_slim_app(slim_endpoint, shared_secret, moderator_name)

    async with moderator_slim_app:
        # create pubsub session
        session_info = await moderator_slim_app.create_session(
        PySessionConfiguration.Streaming(
            PySessionDirection.BIDIRECTIONAL,
            topic=topic_name,
            moderator=True,
            max_retries=20,
            timeout=datetime.timedelta(seconds=60),
            mls_enabled=True,
        ))
        print(f"Session created: {session_info.id}")

        # invite participants
        for invitee in invitees:
            print(f"Inviting {invitee}")
            await moderator_slim_app.set_route(invitee)
            await moderator_slim_app.invite(session_info, invitee)

        # wait for invites to percolate
        await asyncio.sleep(5)

        # publish message to kick off the group chat
        print(f"Publishing message to {topic_name}")
        await moderator_slim_app.publish(session_info, "Hello everyone!".encode(), topic_name)

        # collect replies over 10 seconds
        replies = await collect_messages(moderator_slim_app, session_info.id, duration=10.0)

        # clean up
        # await moderator_slim_app.leave(session_info.id)

        return replies
 
async def run_participant(slim_endpoint, shared_secret: str, participant_name: PyName,  
                          reply_to: PyName, reply_messages: Iterable[str]):
    # init slim client
    slim_app = await create_slim_app(slim_endpoint, shared_secret, participant_name)

    async with slim_app:
        # listen for incoming sessions
        print(f"[participant] listening - locator: {participant_name}")
        recv_session, _ = await slim_app.receive()
        print(f"received session: {recv_session.id}")
        print(f"from: {recv_session.source_name}")
        print(f"to:   {recv_session.destination_name}")

        send_task = asyncio.create_task(send_messages(reply_messages, slim_app, recv_session, reply_to))
        collect_task = asyncio.create_task(collect_messages(slim_app, recv_session.id, duration=10.0))

        # try:
        # send messages to recipient
        await send_task
        # at the same time, collect session messages
        replies = await collect_task
        # finally:
        #     await slim_app.leave(recv_session.id)

        return replies