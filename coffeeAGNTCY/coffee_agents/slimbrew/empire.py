import asyncio
import datetime
import os
from dotenv import load_dotenv

from slim_bindings import (
    PyName,
    PySessionConfiguration,
    PySessionDirection,
)

from common import create_slim_app

async def run_moderator(secret: str, channel: PyName, invitees: list[PyName]) -> tuple[list[str], Exception]:
    local_name = PyName("agntcy", "slimbrew", "moderator")
    moderator_slim_app = await create_slim_app(secret, local_name)
    async with moderator_slim_app:
        # create session
        session_info = await moderator_slim_app.create_session(
        PySessionConfiguration.Streaming(
            PySessionDirection.BIDIRECTIONAL,
            topic=channel,
            moderator=False,
            max_retries=20,
            timeout=datetime.timedelta(seconds=60),
            mls_enabled=False,
        ))
        print(f"Session created: {session_info.id}")

        # invite participants
        for invitee in invitees:
            print(f"Inviting {invitee}")
            await moderator_slim_app.set_route(invitee)
            await moderator_slim_app.invite(session_info, invitee)

        await asyncio.sleep(5)

        # publish message
        print(f"Publishing message to {channel}")
        await moderator_slim_app.publish(session_info, "Hello everyone!".encode(), channel)

        while True:
            try:
                await asyncio.wait_for(moderator_slim_app.receive(session=session_info.id), timeout=15)
            except TimeoutError:
                print(f"Timed out waiting for messages in session {session_info.id}")
            _, msg = await moderator_slim_app.receive(session=session_info.id)
            print(f"Received message in session {session_info.id}: {msg.decode()}")


if __name__ == "__main__":
    try:
        load_dotenv()
        secret = os.environ.get("SLIM_SHARED_SECRET")
        if not secret:
            raise RuntimeError("SLIM_SHARED_SECRET not set")
        shared_channel = PyName("agntcy", "namespace", "group_channel")
        invitees = [PyName("agntcy", "slimbrew", "coruscant-farm"), PyName("agntcy", "slimbrew", "tatooine-farm")]
        asyncio.run(run_moderator(secret, shared_channel, invitees))
    except KeyboardInterrupt:
        print("Client interrupted by user.")
