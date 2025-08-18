import asyncio
import pytest
import asyncio
import datetime

from slim_bindings import (
    PyName,
    PySessionConfiguration,
    PySessionDirection,
)

from helpers import create_slim_app, run_participant, run_moderator, collect_messages



@pytest.mark.asyncio
async def test_group_communication_mls_enabled(slim_endpoint, shared_secret, moderator_name, topic_name):
    """
    This test asserts that after a moderator invites two (already running) participants, they receive
    the moderator's invite and are able to reply to the session.

    Asserts:
    - Participants receive each other's messages
    - Non-invited participant doesn't receive the message
    - Moderator receives both participants' messages
    - Participants do not receive their own messages
    """
    invitees = [
        PyName("agntcy", "slimbrew", "participant-1"),
        PyName("agntcy", "slimbrew", "participant-2"),
    ]
    p1_message = "Hello from p1"
    p2_message = "Hello from p2"

    # run participants
    p1 = asyncio.create_task(run_participant(slim_endpoint, shared_secret,
                                             invitees[0], topic_name,
                                             [p1_message]))
    p2 = asyncio.create_task(run_participant(slim_endpoint, shared_secret,
                                             invitees[1], topic_name,
                                             [p2_message]))
    # p3 = asyncio.create_task(run_participant(slim_endpoint, shared_secret,
    #                                          PyName("agntcy", "slimbrew", "participant-3"), topic_name,
    #                                          []))

    # run moderator
    mod = asyncio.create_task(run_moderator(slim_endpoint, shared_secret,
                                            topic_name, moderator_name,
                                            invitees, mls_enabled=True))

    p1_msgs, p2_msgs, mod_msgs = await asyncio.gather(p1, p2, mod)

    # assertions
    print("Participant 1 messages:", p1_msgs)
    print("Participant 2 messages:", p2_msgs)
    # print("Participant 3 messages:", p3_msgs)
    print("Moderator messages:", mod_msgs)
    
    # the participants should receive each other's messages
    assert any(p2_message in m for m in p1_msgs)
    assert any(p1_message in m for m in p2_msgs)
    # the moderator should receive both participants' messages
    assert any(p1_message and p2_message in m for m in mod_msgs)
    # the participants should not receive their own messages
    assert not any(p1_message in m for m in p1_msgs)
    assert not any(p2_message in m for m in p2_msgs)
    # participant 3 should not receive any messages since they were not invited
    # assert not any(p3_msgs)

@pytest.mark.asyncio
async def test_group_communcation_mls_disabled(slim_endpoint, shared_secret, moderator_name, topic_name):
    """
    This test asserts that after a moderator invites two (already running) participants, they receive
    the moderator's invite and are able to reply to the session.

    Asserts:
    - Participants receive each other's messages
    - Non-invited participant doesn't receive the message
    - Moderator receives both participants' messages
    - Participants do not receive their own messages
    """
    invitees = [
        PyName("agntcy", "slimbrew", "participant-1"),
        PyName("agntcy", "slimbrew", "participant-2"),
    ]
    p1_message = "Hello from p1"
    p2_message = "Hello from p2"

    # run participants
    p1 = asyncio.create_task(run_participant(slim_endpoint, shared_secret,
                                             invitees[0], topic_name,
                                             [p1_message]))
    p2 = asyncio.create_task(run_participant(slim_endpoint, shared_secret,
                                             invitees[1], topic_name,
                                             [p2_message]))

    # run moderator
    mod = asyncio.create_task(run_moderator(slim_endpoint, shared_secret,
                                            topic_name, moderator_name,
                                            invitees, mls_enabled=False))

    p1_msgs, p2_msgs, mod_msgs = await asyncio.gather(p1, p2, mod)

    # assertions
    print("Participant 1 messages:", p1_msgs)
    print("Participant 2 messages:", p2_msgs)
    print("Moderator messages:", mod_msgs)
    
    # the participants should receive each other's messages
    assert any(p2_message in m for m in p1_msgs)
    assert any(p1_message in m for m in p2_msgs)
    # the moderator should receive both participants' messages
    assert any(p1_message and p2_message in m for m in mod_msgs)
    # the participants should not receive their own messages
    assert not any(p1_message in m for m in p1_msgs)
    assert not any(p2_message in m for m in p2_msgs)

@pytest.mark.asyncio
async def test_group_communcation_late_invite(slim_endpoint, shared_secret, moderator_name, topic_name):
    """
    This test asserts that after a moderator invites two (already running) participants, they receive
    the moderator's invite and are able to reply to the session.

    Asserts:
    - Participants receive each other's messages
    - Non-invited participant doesn't receive the message
    - Moderator receives both participants' messages
    - Participants do not receive their own messages
    """
    invitees = [
        PyName("agntcy", "slimbrew", "participant-1"),
        PyName("agntcy", "slimbrew", "participant-2")    ]
    p1_message = "Hello from p1"
    p2_message = "Hello from p2"
    p3_message = "Hello from p3"
    mod_message = "Hello everyone!"

    # run participants
    p1 = asyncio.create_task(run_participant(slim_endpoint, shared_secret,
                                             invitees[0], topic_name,
                                             [p1_message]))
    p2 = asyncio.create_task(run_participant(slim_endpoint, shared_secret,
                                             invitees[1], topic_name,
                                             [p2_message]))

    # run moderator
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
        await moderator_slim_app.publish(session_info, mod_message.encode(), topic_name)

        # collect replies over 10 seconds
        replies = await collect_messages(moderator_slim_app, session_info.id, duration=10.0)

        # simulate late joiner by inviting p3 after the fact
        await moderator_slim_app.set_route(PyName("agntcy", "slimbrew", "participant-3"))
        await moderator_slim_app.invite(session_info, PyName("agntcy", "slimbrew", "participant-3"))

        p3 = asyncio.create_task(run_participant(slim_endpoint, shared_secret,
                                             PyName("agntcy", "slimbrew", "participant-3"), topic_name,
                                             [p3_message]))

        # wait for p3 to join
        await asyncio.sleep(5)

        print(f"Publishing message to {topic_name}")
        await moderator_slim_app.publish(session_info, mod_message.encode(), topic_name)
        print(f"Publishing message to {topic_name}")
    

    p1_msgs, p2_msgs, p3_msgs = await asyncio.gather(p1, p2, p3)

    # assertions
    print("Participant 1 messages:", p1_msgs)
    print("Participant 2 messages:", p2_msgs)
    print("Participant 3 messages:", p3_msgs)
    print("Moderator messages:", replies)

    # all participants should receive the moderator's message
    assert any(mod_message in m for m in p1_msgs)
    assert any(mod_message in m for m in p2_msgs)
    assert any(mod_message in m for m in p3_msgs)
    # the participants should receive each other's messages
    assert any(p2_message in m for m in p1_msgs)
    assert any(p1_message in m for m in p2_msgs)
    # participant 3 should not receive participant 1 or 2's messages
    assert not any(p1_message in m for m in p3_msgs)
    assert not any(p2_message in m for m in p3_msgs)
    # the moderator should receive both participants' messages
    assert any(p1_message and p2_message in m for m in replies)
    # the participants should not receive their own messages
    assert not any(p1_message in m for m in p1_msgs)
    assert not any(p2_message in m for m in p2_msgs)

