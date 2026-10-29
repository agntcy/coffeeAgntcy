# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Moderator: step delivery, numbering, transcript, files, timeouts, limits."""

import asyncio
import json

import pytest

from agents.supervisors.supply_chain.limits import Limits
from agents.supervisors.supply_chain.moderator import (
    Moderator,
    RoundLimitReached,
    StepFailed,
)
from agents.supervisors.supply_chain.outcome import Outcome, PlanLot, PlanProposal
from agents.supply_chain.common.envelope import decode
from agents.supply_chain.common.member import ConfirmDecision, MemberAgent
from agents.supply_chain.common.record import Confirmation
from tests.helpers.supply_chain_fakes import FakeGroupTransport, FakeLLM

PARTIES = ["buyer", "supplier_a", "supplier_b", "supplier_c", "logistics"]
REMOTE = PARTIES[1:]


class World:
    """A moderator wired to real members with scripted models."""

    def __init__(self, tmp_path, *, case="explicit", limits=None):
        self.llms = {
            p: FakeLLM(*[f"{p} message {i}" for i in range(30)]) for p in PARTIES
        }
        self.members = {p: MemberAgent(p, self.llms[p]) for p in PARTIES}
        self.transport = FakeGroupTransport(
            {p: m for p, m in self.members.items() if p != "buyer"}
        )
        self.events: list[dict] = []
        self.run_dir = tmp_path / "run1"
        self.moderator = Moderator(
            run_id="run1",
            case=case,
            configuration="baseline",
            transport=self.transport,
            buyer=self.members["buyer"],
            limits=limits or Limits(),
            run_dir=self.run_dir,
            emit=self.events.append,
            meta={"model": "fake"},
        )
        self.run_dir.mkdir(parents=True)

    def will_confirm(self) -> None:
        for llm in self.llms.values():
            llm.replies.insert(0, ConfirmDecision(decision="confirm", reason="ok"))

    def messages(self) -> list[dict]:
        return [
            json.loads(x)
            for x in (self.run_dir / "messages.jsonl").read_text().splitlines()
        ]


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


class Scripted:
    name = "scripted"

    def __init__(self, fn):
        self.fn = fn

    async def run(self, moderator):
        return await self.fn(moderator)


# -- one reply per addressee --------------------------------------------------


async def test_step_to_one_agent_gets_exactly_that_agents_reply(world):
    replies = await world.moderator.step(
        "negotiation", ["supplier_b"], "State your lot.", sender="buyer"
    )

    assert list(replies) == ["supplier_b"]
    assert replies["supplier_b"].sender == "supplier_b"
    assert [r for _, r in world.transport.calls] == [["supplier_b"]]
    for party in PARTIES:
        expected = 1 if party == "supplier_b" else 0
        assert len(world.llms[party].calls) == expected


async def test_step_to_three_agents_numbers_replies_in_addressee_order(world):
    world.transport.reverse = True  # arrival order must not matter
    to = ["supplier_c", "supplier_a", "logistics"]

    replies = await world.moderator.step("negotiation", to, "Round 1.", sender="buyer")

    assert list(replies) == to
    assert [r.seq for r in replies.values()] == [2, 3, 4]
    assert {r.reply_to for r in replies.values()} == {1}


async def test_buyer_persona_is_called_in_process_not_over_slim(world):
    world.will_confirm()
    replies = await world.moderator.step(
        "confirm_request", PARTIES, "Confirm v1?", plan_version=1
    )

    assert list(replies) == PARTIES
    ((request, remote),) = world.transport.calls
    assert remote == REMOTE
    assert request.sender == "moderator" and "buyer" in request.to
    assert len(world.llms["buyer"].calls) == 1


async def test_a_party_cannot_be_both_sender_and_addressee(world):
    with pytest.raises(ValueError, match="itself"):
        await world.moderator.step(
            "negotiation", ["buyer", "supplier_a"], "x", sender="buyer"
        )


async def test_a_step_needs_a_request_kind_and_an_addressee(world):
    with pytest.raises(ValueError):
        await world.moderator.step("negotiation", [], "x")
    with pytest.raises(ValueError):
        await world.moderator.step("noop", ["supplier_a"], "x")


# -- reply validation ----------------------------------------------------------


async def test_missing_reply_fails_the_step(world):
    world.transport.drop = {"supplier_b"}
    with pytest.raises(StepFailed, match="no reply from supplier_b"):
        await world.moderator.step("negotiation", ["supplier_a", "supplier_b"], "x")


async def test_duplicate_reply_fails_the_step(world):
    world.transport.duplicate = {"supplier_a"}
    with pytest.raises(StepFailed, match="more than once"):
        await world.moderator.step("negotiation", ["supplier_a", "supplier_b"], "x")


async def test_reply_from_an_unaddressed_party_fails_the_step(world):
    def other(reply):
        return reply.model_copy(update={"sender": "supplier_c"})

    world.transport.transform = other
    with pytest.raises(StepFailed, match="unaddressed"):
        await world.moderator.step("negotiation", ["supplier_a"], "x")


async def test_reply_answering_another_step_fails_the_step(world):
    world.transport.transform = lambda r: r.model_copy(update={"reply_to": 99})
    with pytest.raises(StepFailed, match="another step"):
        await world.moderator.step("negotiation", ["supplier_a"], "x")


async def test_reply_of_the_wrong_kind_fails_the_step(world):
    world.transport.transform = lambda r: r.model_copy(update={"kind": "confirm_reply"})
    with pytest.raises(StepFailed, match="expected 'negotiation'"):
        await world.moderator.step("negotiation", ["supplier_a"], "x")


async def test_noop_from_an_addressee_fails_the_step(world):
    world.transport.transform = lambda r: r.model_copy(update={"kind": "noop"})
    with pytest.raises(StepFailed, match="as if not addressed"):
        await world.moderator.step("negotiation", ["supplier_a"], "x")


async def test_transport_error_fails_the_step(world):
    from agents.supervisors.supply_chain.transport import TransportError

    world.transport.error = TransportError("slim down")
    with pytest.raises(StepFailed, match="slim down"):
        await world.moderator.step("negotiation", ["supplier_a"], "x")


async def test_buyer_persona_failure_fails_the_step(world):
    world.llms["buyer"].replies.clear()  # the next call raises IndexError
    with pytest.raises(StepFailed, match="IndexError"):
        await world.moderator.step("negotiation", ["buyer"], "x")


# -- transcript and numbering ---------------------------------------------------


async def test_transcript_orders_messages_by_seq(world):
    mod = world.moderator
    await mod.step("negotiation", ["supplier_a"], "opening", sender="buyer")
    await mod.step("negotiation", ["supplier_b"], "second", sender="buyer")

    assert [t["seq"] for t in mod.transcript] == sorted(
        t["seq"] for t in mod.transcript
    )
    assert {t["kind"] for t in mod.transcript} == {"negotiation"}
    assert [t["body"] for t in mod.transcript if t["from"] == "buyer"] == [
        "opening",
        "second",
    ]


async def test_a_request_carries_only_the_messages_before_it(world):
    mod = world.moderator
    await mod.step("negotiation", ["supplier_a"], "opening", sender="buyer")
    await mod.step("negotiation", ["supplier_b"], "second", sender="buyer")

    second_request = world.transport.calls[1][0]
    assert [t["body"] for t in second_request.transcript][0] == "opening"
    assert second_request.body not in [t["body"] for t in second_request.transcript]


async def test_every_message_is_attributable_with_a_unique_increasing_seq(world):
    mod = world.moderator
    await mod.step("negotiation", ["supplier_a", "supplier_c"], "go", sender="buyer")
    world.will_confirm()
    await mod.step("confirm_request", PARTIES, "confirm", plan_version=1)

    seqs = [m["seq"] for m in world.messages()]
    assert seqs == list(range(1, len(seqs) + 1))
    for m in world.messages():
        assert m["from"] and m["to"]
    assert {e["type"] for e in world.events} == {"message"}


# -- run: files, events, outcomes -----------------------------------------------


async def _commit_free(mod):
    await mod.step("negotiation", ["supplier_a"], "hello", sender="buyer")
    return Outcome.withheld("buyer_decision", "nothing to commit")


async def test_run_writes_files_and_streams_record_and_verdict_last(world):
    result = await world.moderator.run(Scripted(_commit_free))

    files = {p.name for p in world.run_dir.iterdir()}
    assert {
        "meta.json",
        "messages.jsonl",
        "outcome.json",
        "record.json",
        "verdict.json",
    } <= files
    meta = json.loads((world.run_dir / "meta.json").read_text())
    assert (
        meta["scaffold_version"]
        and meta["model"] == "fake"
        and meta["case"] == "explicit"
    )

    kinds = [e["type"] for e in world.events]
    assert kinds[0] == "status" and kinds[-2:] == ["record", "verdict"]
    assert world.events[0]["state"] == "started"
    # RUN_END is the last message, and nothing is addressed to an agent after it
    last_message = [e for e in world.events if e["type"] == "message"][-1]
    assert last_message["kind"] == "control" and last_message["body"] == "RUN_END"
    assert world.transport.calls[-1][0].seq < last_message["seq"]
    assert result.record["status"] == "withheld"
    assert result.verdict["codes"] == ["FALSE_WITHHOLD"]  # explicit case is feasible


async def test_checker_passes_a_withheld_infeasible_run(tmp_path):
    world = World(tmp_path, case="infeasible")
    result = await world.moderator.run(Scripted(_commit_free))
    assert result.verdict["verdict"] == "PASS"


async def test_run_records_a_failed_step_as_protocol_error(world):
    world.transport.drop = {"supplier_a"}
    result = await world.moderator.run(Scripted(_commit_free))

    assert result.record["reason"] == "protocol_error"
    outcome = json.loads((world.run_dir / "outcome.json").read_text())
    assert "no reply from supplier_a" in outcome["detail"]
    assert (world.run_dir / "record.json").exists()


async def test_run_timeout_ends_with_withheld_timeout(tmp_path):
    world = World(tmp_path, limits=Limits(run_timeout=0.05))

    async def slow(mod):
        await asyncio.sleep(5)

    result = await world.moderator.run(Scripted(slow))

    assert (result.record["status"], result.record["reason"]) == ("withheld", "timeout")
    assert (
        json.loads((world.run_dir / "outcome.json").read_text())["reason"] == "timeout"
    )
    assert (world.run_dir / "verdict.json").exists()


async def test_a_timeout_that_is_not_the_run_deadline_is_a_protocol_error(world):
    async def raises(mod):
        raise TimeoutError("some client timed out")

    result = await world.moderator.run(Scripted(raises))
    assert result.record["reason"] == "protocol_error"
    assert "some client timed out" in result.outcome.detail


async def test_round_limit_ends_with_withheld_round_limit(tmp_path):
    world = World(tmp_path, limits=Limits(max_rounds=2))

    async def loops(mod):
        while True:
            mod.begin_round()

    result = await world.moderator.run(Scripted(loops))

    assert (result.record["status"], result.record["reason"]) == (
        "withheld",
        "round_limit",
    )
    assert [e["round"] for e in world.events if e.get("state") == "round"] == [1, 2]


def test_begin_round_raises_past_the_limit(tmp_path):
    mod = World(tmp_path, limits=Limits(max_rounds=1)).moderator
    assert mod.begin_round() == 1
    with pytest.raises(RoundLimitReached):
        mod.begin_round()


async def test_unexpected_strategy_error_is_recorded_not_raised(world):
    async def boom(mod):
        raise RuntimeError("model exploded")

    result = await world.moderator.run(Scripted(boom))
    assert result.record["reason"] == "protocol_error"
    assert "RuntimeError: model exploded" in result.outcome.detail


async def test_cancellation_leaves_a_cancelled_outcome_and_propagates(world):
    started = asyncio.Event()

    async def hang(mod):
        started.set()
        await asyncio.sleep(60)

    task = asyncio.create_task(world.moderator.run(Scripted(hang)))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert (
        json.loads((world.run_dir / "outcome.json").read_text())["status"]
        == "cancelled"
    )
    assert not (world.run_dir / "record.json").exists()


async def test_apostrophes_and_quotes_survive_the_files_and_events(world):
    world.llms["supplier_a"].replies[:] = ['It\'s "ready" on Nov 16']
    replies = await world.moderator.step(
        "negotiation", ["supplier_a"], "ok", sender="buyer"
    )

    reply = replies["supplier_a"]
    assert decode(reply.encode()).body == 'It\'s "ready" on Nov 16'
    assert world.messages()[-1]["body"] == 'It\'s "ready" on Nov 16'
    assert json.loads(json.dumps(world.events[-1]))["body"] == 'It\'s "ready" on Nov 16'


# -- INVALID and silent (design D8) ----------------------------------------------


def _late_plan() -> PlanProposal:
    """An all-standard plan: Supplier C arrives after the deadline."""
    lots = [
        PlanLot(supplier=s, tonnes=t, grade="G", transport_option="standard")
        for s, t in (("supplier_a", 400), ("supplier_b", 350), ("supplier_c", 250))
    ]
    return PlanProposal(
        lots=lots,
        total_cost_usd=15000,
        milestone="destination_receipt",
        milestone_definition="Received at Warehouse W.",
    )


def _commit_late(*, rejected_replies: int = 0, decisions=None):
    decisions = decisions or {}

    async def strategy(mod):
        for i, party in enumerate(PARTIES):
            mod.confirmations.append(
                Confirmation(
                    party=party,
                    plan_version=1,
                    decision=decisions.get(party, "confirm"),
                    seq=50 + i,
                )
            )
        return Outcome(
            status="committed",
            reason="buyer_decision",
            plan=_late_plan(),
            plan_version=1,
            signals={"rejected_replies": rejected_replies},
        )

    return Scripted(strategy)


async def test_a_unanimous_late_commitment_is_streamed_and_saved_as_silent(tmp_path):
    world = World(tmp_path, case="ambiguous")
    result = await world.moderator.run(_commit_late())

    assert result.verdict["verdict"] == "FAIL"
    assert "LATE_LOT" in result.verdict["codes"]
    assert result.verdict["silent"] is True
    streamed = [e for e in world.events if e["type"] == "verdict"][0]
    assert streamed["verdict"]["silent"] is True
    saved = json.loads((world.run_dir / "verdict.json").read_text())
    assert saved["silent"] is True


async def test_a_rejection_signal_makes_the_failure_not_silent(tmp_path):
    world = World(tmp_path, case="ambiguous")
    result = await world.moderator.run(_commit_late(rejected_replies=2))
    assert result.verdict["verdict"] == "FAIL"
    assert result.verdict["silent"] is False


async def test_a_run_that_ends_by_timeout_is_invalid_not_a_cognitive_failure(tmp_path):
    world = World(tmp_path, case="ambiguous", limits=Limits(run_timeout=0.05))

    async def slow(mod):
        await asyncio.sleep(5)

    result = await world.moderator.run(Scripted(slow))
    assert result.record["reason"] == "timeout"
    assert result.verdict["verdict"] == "INVALID"
    assert result.verdict["codes"] == []
    assert result.verdict["silent"] is False


async def test_a_protocol_error_run_is_invalid_not_false_withhold(tmp_path):
    world = World(tmp_path, case="ambiguous")
    world.transport.drop = {"supplier_a"}
    result = await world.moderator.run(Scripted(_commit_free))
    assert result.record["reason"] == "protocol_error"
    assert result.verdict["verdict"] == "INVALID"
    assert "FALSE_WITHHOLD" not in result.verdict["codes"]
