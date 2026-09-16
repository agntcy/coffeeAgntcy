# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from datetime import UTC, datetime, timedelta

import pytest

from common.ioc_mocks.alignment_store import (
    AlignmentAction,
    AlignmentReply,
    AlignmentStart,
    AlignmentStatus,
    AlignmentStore,
)
from common.ioc_mocks.errors import (
    MockStoreConflictError,
    MockStoreValidationError,
)
from common.ioc_mocks.intent_store import IntentStore
from common.ioc_mocks.memory_store import MemoryFactWrite, MemoryStore
from common.ioc_mocks.team_store import (
    PollOpen,
    PollResponseWrite,
    TeamStore,
)

FIXED_TIME = datetime(2026, 9, 16, 8, 0, tzinfo=UTC)


class FixedClock:
    def __init__(self, value: datetime = FIXED_TIME) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


def parameter_id(value: object) -> str | None:
    return value if isinstance(value, str) else None


@pytest.mark.parametrize(
    ("case_id", "keys", "key_contains", "expected_keys"),
    [
        ("all facts", None, None, {"state", "price_per_lb"}),
        ("exact key", ["state"], None, {"state"}),
        ("missing key", ["quantity_lbs"], None, set()),
        ("key substring", None, "price", {"price_per_lb"}),
    ],
    ids=parameter_id,
)
async def test_memory_recall_filters(
    case_id: str,
    keys: list[str] | None,
    key_contains: str | None,
    expected_keys: set[str],
) -> None:
    store = MemoryStore(now=FixedClock())
    await store.retain(
        "instance:order-1",
        [
            MemoryFactWrite(key="state", value="paid", actor="accountant"),
            MemoryFactWrite(key="price_per_lb", value=4.5, actor="farm"),
        ],
    )

    facts = await store.recall("instance:order-1", keys, key_contains)

    assert {fact.key for fact in facts} == expected_keys


async def test_memory_upserts_and_isolates_scopes() -> None:
    store = MemoryStore(now=FixedClock())
    await store.retain(
        "instance:order-1",
        [MemoryFactWrite(key="state", value="created", actor="buyer")],
    )
    await store.retain(
        "instance:order-1",
        [MemoryFactWrite(key="state", value="paid", actor="accountant")],
    )
    await store.retain(
        "instance:order-2",
        [MemoryFactWrite(key="state", value="created", actor="buyer")],
    )

    order_one = await store.dump("instance:order-1")

    assert len(order_one) == 1
    assert order_one[0].value == "paid"
    assert order_one[0].actor == "accountant"
    assert order_one[0].recorded_at == FIXED_TIME


async def test_intent_query_returns_latest_per_actor_and_keeps_history() -> None:
    store = IntentStore(now=FixedClock())
    await store.publish("instance:order-1", "farm", "quote", {"quantity": 1000})
    await store.publish("instance:order-1", "shipper", "route", {})
    latest_farm = await store.publish(
        "instance:order-1",
        "farm",
        "reserve",
        {"quantity": 1000},
    )

    current = await store.query("instance:order-1")
    history = await store.dump("instance:order-1")

    assert {intent.actor for intent in current} == {"farm", "shipper"}
    assert latest_farm.version == 2
    assert len(history) == 3


async def test_team_poll_closes_with_partial_roster() -> None:
    store = TeamStore(now=FixedClock())
    await store.open_poll(
        PollOpen(
            team_id="team-1",
            roles=["farm", "shipper", "accountant"],
        )
    )
    await store.respond(
        PollResponseWrite(
            team_id="team-1",
            actor="farm-agent",
            role="farm",
            accepted=True,
        )
    )
    await store.respond(
        PollResponseWrite(
            team_id="team-1",
            actor="shipper-agent",
            role="shipper",
            accepted=False,
        )
    )

    roster = await store.close_poll("team-1")

    assert roster.bindings == {"farm": "farm-agent"}
    assert roster.declined == ["shipper-agent"]
    assert roster.unfilled == ["shipper", "accountant"]
    assert roster.partial is True


@pytest.mark.parametrize(
    ("case_id", "response_write", "error"),
    [
        (
            "duplicate accepted role",
            PollResponseWrite(
                team_id="team-1",
                actor="second-farm",
                role="farm",
                accepted=True,
            ),
            MockStoreConflictError,
        ),
        (
            "unknown role",
            PollResponseWrite(
                team_id="team-1",
                actor="lawyer",
                role="legal",
                accepted=True,
            ),
            MockStoreValidationError,
        ),
    ],
    ids=parameter_id,
)
async def test_team_poll_rejects_invalid_responses(
    case_id: str,
    response_write: PollResponseWrite,
    error: type[Exception],
) -> None:
    store = TeamStore(now=FixedClock())
    await store.open_poll(PollOpen(team_id="team-1", roles=["farm"]))
    await store.respond(
        PollResponseWrite(
            team_id="team-1",
            actor="first-farm",
            role="farm",
            accepted=True,
        )
    )

    with pytest.raises(error):
        await store.respond(response_write)


async def test_team_poll_rejects_response_after_deadline() -> None:
    clock = FixedClock()
    store = TeamStore(now=clock)
    await store.open_poll(
        PollOpen(
            team_id="team-1",
            roles=["farm"],
            deadline=FIXED_TIME + timedelta(seconds=1),
        )
    )
    clock.value = FIXED_TIME + timedelta(seconds=2)

    with pytest.raises(MockStoreConflictError):
        await store.respond(
            PollResponseWrite(
                team_id="team-1",
                actor="farm-agent",
                role="farm",
                accepted=True,
            )
        )


async def test_alignment_reaches_agreement() -> None:
    store = AlignmentStore(now=FixedClock())
    await store.start(
        AlignmentStart(
            session_id="alignment-1",
            participants=["brazil", "colombia"],
            goal="Agree coffee terms",
            issues={"grade": ["A", "B"], "unit": ["lb", "kg"]},
        )
    )

    result = await store.decide(
        "alignment-1",
        [
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

    assert result.status is AlignmentStatus.AGREED
    assert result.agreement == {"grade": "A", "unit": "lb"}


async def test_alignment_times_out_at_round_limit() -> None:
    store = AlignmentStore(now=FixedClock())
    await store.start(
        AlignmentStart(
            session_id="alignment-1",
            participants=["brazil", "colombia"],
            goal="Agree coffee terms",
            issues={"grade": ["A", "B"]},
            max_rounds=1,
        )
    )

    result = await store.decide(
        "alignment-1",
        [
            AlignmentReply(
                participant_id="brazil",
                action=AlignmentAction.COUNTER_OFFER,
                offer={"grade": "B"},
            ),
            AlignmentReply(
                participant_id="colombia",
                action=AlignmentAction.ACCEPT,
            ),
        ],
    )

    assert result.status is AlignmentStatus.TIMEOUT


async def test_alignment_rejects_offer_outside_agenda() -> None:
    store = AlignmentStore(now=FixedClock())
    await store.start(
        AlignmentStart(
            session_id="alignment-1",
            participants=["brazil", "colombia"],
            goal="Agree coffee terms",
            issues={"grade": ["A", "B"]},
        )
    )

    with pytest.raises(MockStoreValidationError):
        await store.decide(
            "alignment-1",
            [
                AlignmentReply(
                    participant_id="brazil",
                    action=AlignmentAction.COUNTER_OFFER,
                    offer={"grade": "C"},
                ),
                AlignmentReply(
                    participant_id="colombia",
                    action=AlignmentAction.ACCEPT,
                ),
            ],
        )
