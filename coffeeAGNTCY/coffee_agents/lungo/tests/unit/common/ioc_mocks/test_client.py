# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import httpx

from common.ioc_mocks.alignment_store import (
    AlignmentAction,
    AlignmentDecide,
    AlignmentReply,
    AlignmentStart,
    AlignmentStatus,
)
from common.ioc_mocks.app import create_app
from common.ioc_mocks.client import IocMockClient
from common.ioc_mocks.intent_store import IntentPublish
from common.ioc_mocks.memory_store import (
    MemoryFactWrite,
    MemoryRecall,
    MemoryRetain,
)
from common.ioc_mocks.team_store import PollOpen, PollResponseWrite


def create_transport() -> httpx.ASGITransport:
    return httpx.ASGITransport(app=create_app())


async def test_health_endpoint() -> None:
    async with httpx.AsyncClient(
        transport=create_transport(),
        base_url="http://test",
    ) as client:
        response = await client.get("/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_memory_client_round_trip() -> None:
    async with IocMockClient(
        "http://test",
        transport=create_transport(),
    ) as client:
        await client.retain_memory(
            MemoryRetain(
                scope_id="instance:order-1",
                facts=[
                    MemoryFactWrite(
                        key="state",
                        value="paid",
                        actor="accountant",
                    )
                ],
            )
        )
        recalled = await client.recall_memory(
            MemoryRecall(scope_id="instance:order-1", keys=["state"])
        )

    assert len(recalled) == 1
    assert recalled[0].value == "paid"


async def test_intent_client_round_trip() -> None:
    async with IocMockClient(
        "http://test",
        transport=create_transport(),
    ) as client:
        await client.publish_intent(
            IntentPublish(
                scope_id="instance:order-1",
                actor="farm",
                goal="reserve inventory",
            )
        )
        intents = await client.query_intents("instance:order-1", actor="farm")

    assert len(intents) == 1
    assert intents[0].goal == "reserve inventory"


async def test_team_client_round_trip() -> None:
    async with IocMockClient(
        "http://test",
        transport=create_transport(),
    ) as client:
        await client.open_team_poll(
            PollOpen(team_id="team-1", roles=["farm", "shipper"])
        )
        await client.respond_to_team_poll(
            PollResponseWrite(
                team_id="team-1",
                actor="farm-agent",
                role="farm",
                accepted=True,
            )
        )
        roster = await client.close_team_poll("team-1")
        poll = await client.get_team_poll("team-1")

    assert roster.bindings == {"farm": "farm-agent"}
    assert roster.unfilled == ["shipper"]
    assert poll.roster == roster


async def test_alignment_client_round_trip() -> None:
    async with IocMockClient(
        "http://test",
        transport=create_transport(),
    ) as client:
        await client.start_alignment(
            AlignmentStart(
                session_id="alignment-1",
                participants=["brazil", "colombia"],
                goal="Agree grade",
                issues={"grade": ["A", "B"]},
            )
        )
        result = await client.decide_alignment(
            AlignmentDecide(
                session_id="alignment-1",
                replies=[
                    AlignmentReply(
                        participant_id="brazil",
                        action=AlignmentAction.ACCEPT,
                    ),
                    AlignmentReply(
                        participant_id="colombia",
                        action=AlignmentAction.ACCEPT,
                    ),
                ],
            )
        )
        session = await client.get_alignment("alignment-1")

    assert result.status is AlignmentStatus.AGREED
    assert session.rounds[-1].agreement == {"grade": "A"}
