import asyncio
import pytest

from slim_bindings import PyName

from helpers import run_participant, run_moderator

@pytest.mark.asyncio
async def test_reply_to_destination(slim_endpoint, shared_secret, moderator_name, topic_name):
    invitees = [
        PyName("agntcy", "slimbrew", "participant-1"),
        PyName("agntcy", "slimbrew", "participant-2"),
    ]

    # run participants
    p1 = asyncio.create_task(run_participant(slim_endpoint, shared_secret,
                                             invitees[0], topic_name,
                                             ["Hello from p1"]))
    p2 = asyncio.create_task(run_participant(slim_endpoint, shared_secret,
                                             invitees[1], topic_name,
                                             ["Hello from p2"]))

    # run moderator
    mod = asyncio.create_task(run_moderator(slim_endpoint, shared_secret,
                                            topic_name, moderator_name,
                                            invitees))

    p1_msgs, p2_msgs, mod_msgs = await asyncio.gather(p1, p2, mod)

    # assertions
    print("Participant 1 messages:", p1_msgs)
    print("Participant 2 messages:", p2_msgs)
    print("Moderator messages:", mod_msgs)
    assert any("Hello from p2" in m for m in p1_msgs)
    assert any("Hello from p1" in m for m in p2_msgs)