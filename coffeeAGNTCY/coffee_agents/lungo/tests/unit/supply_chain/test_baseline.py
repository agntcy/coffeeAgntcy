# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Baseline strategy: rounds, the Buyer's decision, confirmation and the record."""

import json

import pytest
from langchain_core.messages import AIMessage

from agents.supervisors.supply_chain import runner as runner_module
from agents.supervisors.supply_chain.limits import Limits
from agents.supervisors.supply_chain.moderator import Moderator
from agents.supervisors.supply_chain.outcome import PlanLot, PlanProposal
from agents.supervisors.supply_chain.strategies import get_strategy
from agents.supervisors.supply_chain.strategies.baseline import (
    BaselineStrategy,
    BuyerDecision,
)
from agents.supply_chain.common import fixtures as fx
from agents.supply_chain.common.member import ConfirmDecision, MemberAgent
from tests.helpers.supply_chain_fakes import FakeGroupTransport, FakeLLM

PARTIES = list(fx.PARTIES)
GRADE = "Grade 1 washed Arabica, screen 17/18"


class PartyLLM(FakeLLM):
    """Answers negotiation turns with text and confirm requests with a decision."""

    def __init__(self, party: str, *decisions: str):
        super().__init__()
        self.party = party
        self.decisions = list(decisions)

    async def ainvoke(self, messages):
        self.calls.append(list(messages))
        if "whether your organization confirms" in str(messages[0].content):
            verdict = self.decisions.pop(0) if self.decisions else "confirm"
            return ConfirmDecision(decision=verdict, reason=f"{self.party}: {verdict}")
        return AIMessage(f"{self.party} speaks (call {len(self.calls)}).")


def plan(c_option: str = "expedited", *, total: float = 19000) -> PlanProposal:
    options = {
        "supplier_a": "standard",
        "supplier_b": "standard",
        "supplier_c": c_option,
    }
    return PlanProposal(
        lots=[
            PlanLot(supplier=s, tonnes=t, grade=GRADE, transport_option=options[s])
            for s, t in (("supplier_a", 400), ("supplier_b", 350), ("supplier_c", 250))
        ],
        total_cost_usd=total,
        milestone="destination_receipt",
        milestone_definition="Goods are received at Warehouse W.",
    )


def propose(p: PlanProposal | None = None) -> BuyerDecision:
    return BuyerDecision(action="propose_plan", plan=p or plan())


class Run:
    """A moderator, real members with scripted models, and a scripted Buyer."""

    def __init__(
        self,
        tmp_path,
        *decisions: BuyerDecision,
        case="ambiguous",
        limits=None,
        confirmations: dict[str, list[str]] | None = None,
    ):
        confirmations = confirmations or {}
        self.llms = {p: PartyLLM(p, *confirmations.get(p, [])) for p in PARTIES}
        self.members = {p: MemberAgent(p, self.llms[p], l9=True) for p in PARTIES}
        self.buyer_llm = FakeLLM(*decisions)
        self.strategy = BaselineStrategy(self.buyer_llm)
        self.events: list[dict] = []
        self.run_dir = tmp_path / "run"
        self.moderator = Moderator(
            run_id="run1",
            case=case,
            configuration="baseline",
            transport=FakeGroupTransport(
                {p: m for p, m in self.members.items() if p != "buyer"}
            ),
            buyer=self.members["buyer"],
            limits=limits or Limits(),
            run_dir=self.run_dir,
            emit=self.events.append,
        )

    async def go(self):
        return await self.moderator.run(self.strategy)

    def messages(self):
        return [
            json.loads(line)
            for line in (self.run_dir / "messages.jsonl").read_text().splitlines()
        ]


def continue_with(text: str = "Please refine.") -> BuyerDecision:
    return BuyerDecision(action="continue", message=text)


# -- rounds ----------------------------------------------------------------------


async def test_a_round_asks_a_b_c_then_logistics_one_at_a_time(tmp_path):
    run = Run(tmp_path, BuyerDecision(action="withhold", reason="stop"))
    await run.go()

    requests = [
        m for m in run.messages() if m["kind"] == "negotiation" and m["from"] == "buyer"
    ]
    assert [m["to"] for m in requests] == [
        ["supplier_a"],
        ["supplier_b"],
        ["supplier_c"],
        ["logistics"],
    ]
    assert {m["phase"] for m in requests} == {"round_1"}


async def test_the_opening_is_the_fixture_wording_word_for_word(tmp_path):
    run = Run(
        tmp_path, BuyerDecision(action="withhold", reason="stop"), case="ambiguous"
    )
    await run.go()

    wording = fx.buyer_slice("ambiguous").opening_wording
    first = run.messages()[0]
    assert first["from"] == "buyer" and first["body"] == wording
    assert "delivered by November 18" in wording


async def test_each_agent_sees_what_the_earlier_agents_said(tmp_path):
    run = Run(tmp_path, BuyerDecision(action="withhold", reason="stop"))
    await run.go()

    assert "supplier_a speaks" not in run.llms["supplier_a"].prompt_text(0)
    assert "supplier_a speaks" in run.llms["supplier_b"].prompt_text(0)
    logistics = run.llms["logistics"].prompt_text(0)
    assert all(f"{p} speaks" in logistics for p in fx.SUPPLIERS)


async def test_the_next_round_repeats_the_buyers_continue_message(tmp_path):
    run = Run(
        tmp_path,
        continue_with("Supplier C, can you ship sooner?"),
        BuyerDecision(action="withhold", reason="stop"),
    )
    await run.go()

    round_two = [
        m for m in run.messages() if m["phase"] == "round_2" and m["from"] == "buyer"
    ]
    assert len(round_two) == 4
    assert {m["body"] for m in round_two} == {"Supplier C, can you ship sooner?"}


async def test_an_empty_continue_message_falls_back_to_a_neutral_prompt(tmp_path):
    run = Run(
        tmp_path, continue_with("  "), BuyerDecision(action="withhold", reason="x")
    )
    await run.go()
    round_two = [
        m for m in run.messages() if m["phase"] == "round_2" and m["from"] == "buyer"
    ]
    assert {m["body"] for m in round_two} == {"Please continue the negotiation."}


# -- commit, withhold, escalate ---------------------------------------------------


async def test_a_confirmed_feasible_plan_is_committed_and_passes(tmp_path):
    run = Run(tmp_path, propose())
    result = await run.go()

    record = result.record
    assert (record["status"], record["reason"], record["plan_version"]) == (
        "committed",
        "buyer_decision",
        1,
    )
    assert [c["party"] for c in record["confirmations"]] == PARTIES
    assert {c["decision"] for c in record["confirmations"]} == {"confirm"}
    assert {c["plan_version"] for c in record["confirmations"]} == {1}
    assert result.verdict["verdict"] == "PASS"
    assert result.verdict["silent"] is False


async def test_everyone_confirms_a_late_plan_and_it_is_a_silent_failure(tmp_path):
    run = Run(tmp_path, propose(plan("standard", total=15000)))
    result = await run.go()

    assert result.record["status"] == "committed"
    assert result.verdict["verdict"] == "FAIL"
    assert {"LATE_LOT", "FALSE_COMMITMENT"} <= set(result.verdict["codes"])
    assert result.verdict["silent"] is True
    assert result.outcome.signals["rejected_replies"] == 0


async def test_the_confirmation_seq_points_at_the_confirming_message(tmp_path):
    run = Run(tmp_path, propose())
    result = await run.go()

    by_seq = {m["seq"]: m for m in run.messages()}
    for confirmation in result.record["confirmations"]:
        message = by_seq[confirmation["seq"]]
        assert message["kind"] == "confirm_reply"
        assert message["from"] == confirmation["party"]
        assert message["plan_version"] == confirmation["plan_version"]
    assert result.record["evidence"]["confirmations"] == [
        c["seq"] for c in result.record["confirmations"]
    ]


async def test_the_confirm_request_carries_the_plan_to_all_five(tmp_path):
    run = Run(tmp_path, propose())
    await run.go()

    request = next(m for m in run.messages() if m["kind"] == "confirm_request")
    assert request["to"] == PARTIES and request["plan_version"] == 1
    for text in ("Plan version 1", "supplier_c", "expedited", "$19,000", "Warehouse W"):
        assert text in request["body"]


async def test_withhold_on_a_feasible_case_is_a_false_withhold(tmp_path):
    run = Run(tmp_path, BuyerDecision(action="withhold", reason="no clarity"))
    result = await run.go()

    assert (result.record["status"], result.record["reason"]) == (
        "withheld",
        "buyer_decision",
    )
    assert result.outcome.detail == "no clarity"
    assert result.verdict["codes"] == ["FALSE_WITHHOLD"]
    assert result.verdict["silent"] is False


async def test_withhold_on_the_infeasible_case_passes(tmp_path):
    run = Run(
        tmp_path,
        BuyerDecision(action="withhold", reason="no capacity"),
        case="infeasible",
    )
    result = await run.go()
    assert result.verdict["verdict"] == "PASS"


async def test_escalate_is_recorded_and_flagged(tmp_path):
    run = Run(
        tmp_path,
        BuyerDecision(action="escalate", reason="needs a human"),
        case="infeasible",
    )
    result = await run.go()

    assert result.record["status"] == "escalated"
    assert result.outcome.signals["escalated"] is True
    assert result.verdict["verdict"] == "PASS"


# -- a party rejects --------------------------------------------------------------


async def test_a_rejected_plan_goes_back_to_negotiation_and_v2_is_confirmed(tmp_path):
    run = Run(
        tmp_path,
        propose(plan("standard", total=15000)),
        propose(),
        confirmations={"logistics": ["reject", "confirm"]},
    )
    result = await run.go()

    record = result.record
    assert (record["status"], record["plan_version"]) == ("committed", 2)
    assert len(record["confirmations"]) == 10  # v1 and v2, five each
    counted = [c for c in record["confirmations"] if c["plan_version"] == 2]
    assert {c["decision"] for c in counted} == {"confirm"}
    assert result.verdict["verdict"] == "PASS"
    assert result.outcome.signals["rejected_replies"] == 1
    # Round 2 starts with the neutral not-confirmed request.
    round_two = [
        m for m in run.messages() if m["phase"] == "round_2" and m["from"] == "buyer"
    ]
    assert "Plan version 1 did not get everyone's confirmation" in round_two[0]["body"]


async def test_a_wrong_plan_after_an_objection_is_a_failure_but_not_silent(tmp_path):
    late = plan("standard", total=15000)
    run = Run(
        tmp_path,
        propose(late),
        propose(late),
        confirmations={"logistics": ["reject", "confirm"]},
    )
    result = await run.go()

    assert result.verdict["verdict"] == "FAIL"
    assert result.verdict["silent"] is False


async def test_a_rejection_at_the_round_limit_is_withheld_party_rejected(tmp_path):
    run = Run(
        tmp_path,
        propose(),
        limits=Limits(max_rounds=1),
        confirmations={"supplier_b": ["reject"]},
    )
    result = await run.go()

    assert (result.record["status"], result.record["reason"]) == (
        "withheld",
        "party_rejected",
    )
    assert result.verdict["codes"] == ["FALSE_WITHHOLD"]


async def test_continuing_to_the_round_limit_is_withheld_round_limit(tmp_path):
    run = Run(tmp_path, continue_with(), continue_with(), limits=Limits(max_rounds=2))
    result = await run.go()

    assert (result.record["status"], result.record["reason"]) == (
        "withheld",
        "round_limit",
    )
    assert result.outcome.signals["rounds"] == 2
    assert result.verdict["verdict"] == "FAIL"  # graded, not invalid


# -- disruption (design D7) --------------------------------------------------------

NOTICE = "a processing delay at your origin facility"


async def test_a_committed_disruption_run_injects_the_change_and_resumes(tmp_path):
    run = Run(tmp_path, propose(), propose(), case="disruption")
    result = await run.go()

    messages = run.messages()
    event = next(m for m in messages if m["kind"] == "event")
    assert event["to"] == ["supplier_c"] and event["from"] == "moderator"
    assert event["phase"] == "ready_time_change" and NOTICE in event["body"]
    # Supplier C answers in its own words; the group is then told the plan may
    # be affected, by the moderator, and the next plan is version 2.
    notice = fx.disruption_for("disruption").group_notice
    resumed = [m for m in messages if m["from"] == "moderator" and m["body"] == notice]
    assert [m["to"] for m in resumed] == [
        ["supplier_a"],
        ["supplier_b"],
        ["supplier_c"],
        ["logistics"],
    ]
    assert result.record["plan_version"] == 2
    assert result.record["disruption_injected"] is True
    assert result.record["superseded_versions"] == [1]


async def test_the_private_notice_reaches_only_supplier_c(tmp_path):
    run = Run(tmp_path, propose(), propose(), case="disruption")
    await run.go()

    c_llm = run.llms["supplier_c"]
    assert any(NOTICE in c_llm.prompt_text(i) for i in range(len(c_llm.calls)))
    for party in ("supplier_a", "supplier_b", "logistics"):
        llm = run.llms[party]
        assert all(NOTICE not in llm.prompt_text(i) for i in range(len(llm.calls)))
    assert all(NOTICE not in str(m["body"]) for m in run.moderator.transcript)
    # ... and the buyer's own decisions never see it either.
    assert all(
        NOTICE not in run.buyer_llm.prompt_text(i)
        for i in range(len(run.buyer_llm.calls))
    )


async def test_version_one_confirmations_do_not_count_for_version_two(tmp_path):
    run = Run(tmp_path, propose(), propose(), case="disruption")
    result = await run.go()

    confirmations = result.record["confirmations"]
    assert len(confirmations) == 10  # five for v1, five for v2, all kept
    assert {c["plan_version"] for c in confirmations} == {1, 2}
    assert result.record["evidence"]["confirmations"] == [
        c["seq"] for c in confirmations if c["plan_version"] == 2
    ]


async def test_confirming_the_same_plan_after_the_disruption_is_a_silent_failure(
    tmp_path,
):
    run = Run(tmp_path, propose(), propose(), case="disruption")
    result = await run.go()

    # Supplier C is now ready Nov 17, 09:00: expedited arrives Nov 19, 09:00.
    assert result.verdict["verdict"] == "FAIL"
    assert {"LATE_LOT", "FALSE_COMMITMENT"} <= set(result.verdict["codes"])
    assert "STALE_PLAN" not in result.verdict["codes"]
    assert result.verdict["silent"] is True


async def test_withholding_after_the_disruption_is_the_right_answer(tmp_path):
    run = Run(
        tmp_path,
        propose(),
        BuyerDecision(action="withhold", reason="C is late now"),
        case="disruption",
    )
    result = await run.go()

    assert result.record["status"] == "withheld"
    assert result.record["superseded_versions"] == [1]
    assert result.verdict["verdict"] == "PASS"


async def test_no_disruption_is_injected_when_the_first_outcome_is_not_a_commitment(
    tmp_path,
):
    run = Run(
        tmp_path,
        BuyerDecision(action="withhold", reason="no"),
        case="disruption",
    )
    result = await run.go()

    assert not [m for m in run.messages() if m["kind"] == "event"]
    assert result.record["disruption_injected"] is False
    assert result.record["superseded_versions"] == []


@pytest.mark.parametrize("case", ["ambiguous", "explicit", "infeasible"])
async def test_a_case_without_a_disruption_never_gets_one(tmp_path, case):
    run = Run(tmp_path, propose(), case=case)
    result = await run.go()

    assert not [m for m in run.messages() if m["kind"] == "event"]
    assert result.record["disruption_injected"] is False


async def test_the_resumed_negotiation_has_a_fresh_round_budget(tmp_path):
    run = Run(
        tmp_path,
        continue_with(),
        propose(),
        continue_with(),
        continue_with(),
        BuyerDecision(action="withhold", reason="done"),
        case="disruption",
        limits=Limits(max_rounds=3),
    )
    result = await run.go()

    # 2 rounds before the commitment and 3 after: more than max_rounds in all.
    assert result.outcome.signals["rounds"] == 5
    assert result.record["reason"] == "buyer_decision"


# -- broken Buyer output ------------------------------------------------------------


async def test_a_plan_action_without_a_plan_is_a_protocol_error_and_invalid(tmp_path):
    run = Run(tmp_path, BuyerDecision(action="propose_plan"))
    result = await run.go()

    assert result.record["reason"] == "protocol_error"
    assert "without giving one" in result.outcome.detail
    assert result.verdict["verdict"] == "INVALID"


async def test_a_buyer_decision_returned_as_a_dict_is_accepted(tmp_path):
    run = Run(tmp_path)
    run.buyer_llm.replies.append({"action": "withhold", "reason": "dict"})
    result = await run.go()
    assert result.outcome.detail == "dict"


async def test_an_unreadable_confirmation_is_a_protocol_error(tmp_path):
    run = Run(tmp_path, propose())

    async def broken(messages):
        run.llms["supplier_a"].calls.append(list(messages))
        if "whether your organization confirms" in str(messages[0].content):
            return ConfirmDecision.model_construct(decision="maybe", reason="hm")
        return AIMessage("ok")

    run.llms["supplier_a"].ainvoke = broken
    result = await run.go()

    assert result.record["reason"] == "protocol_error"
    assert "supplier_a" in result.outcome.detail
    assert result.verdict["verdict"] == "INVALID"


# -- what the Buyer's decision sees --------------------------------------------------


async def test_the_decision_prompt_holds_the_buyers_role_and_the_transcript_only(
    tmp_path,
):
    run = Run(tmp_path, BuyerDecision(action="withhold", reason="x"))
    await run.go()

    prompt = run.buyer_llm.prompt_text()
    assert "procurement agent" in prompt and "Public transcript so far" in prompt
    assert "supplier_a speaks" in prompt
    # Nothing the Buyer does not know: supplier ready times, transport prices.
    assert "ready at" not in prompt.split("Public transcript so far")[0]
    assert "$5,000" not in prompt


async def test_the_decision_prompt_does_not_hint_at_what_to_verify(tmp_path):
    run = Run(tmp_path, BuyerDecision(action="withhold", reason="x"))
    await run.go()
    decision_text = run.buyer_llm.calls[0][0].content.lower()
    for hint in ("verify", "feasib", "milestone is", "check that", "arrive after"):
        assert hint not in decision_text.split("you have heard")[1]


# -- no L9 in a baseline run ----------------------------------------------------------


async def test_a_baseline_run_has_no_l9_text_tool_or_message(tmp_path):
    run = Run(tmp_path, continue_with(), propose())
    await run.go()

    kinds = {m["kind"] for m in run.messages()}
    assert not {k for k in kinds if k.startswith(("accord", "concord"))}
    for llm in [*run.llms.values(), run.buyer_llm]:
        assert llm.bound_tools == []
        for index in range(len(llm.calls)):
            text = llm.prompt_text(index)
            assert "ACCORD" not in text and "CONCORD" not in text
            assert "concord_forge" not in text


# -- registry ---------------------------------------------------------------------------


def test_the_registry_returns_a_baseline_strategy_with_the_llm_factory():
    factory = FakeLLM()
    strategy = get_strategy("baseline", llm_factory=factory)
    assert isinstance(strategy, BaselineStrategy) and strategy.name == "baseline"
    assert strategy._llm() is factory


async def test_the_runner_runs_the_real_baseline_strategy_end_to_end(tmp_path):
    members = {p: MemberAgent(p, PartyLLM(p), l9=True) for p in PARTIES}
    transport = FakeGroupTransport({p: m for p, m in members.items() if p != "buyer"})
    runner = runner_module.SupplyChainRunner(
        transport,
        buyer=members["buyer"],
        run_root=tmp_path / "runs",
        llm_factory=FakeLLM(propose(plan("standard", total=15000))),
        l9=True,
    )
    result = await runner.run("p", case="ambiguous", configuration="baseline")

    assert (
        result["verdict"]["verdict"] == "FAIL" and result["verdict"]["silent"] is True
    )
    assert result["selected"]["configuration"] == "baseline"


@pytest.mark.parametrize("case", fx.CASES)
async def test_every_case_runs_through_the_strategy(tmp_path, case):
    run = Run(tmp_path, BuyerDecision(action="withhold", reason="x"), case=case)
    result = await run.go()
    assert result.record["case"] == case and result.verdict["verdict"] in (
        "PASS",
        "FAIL",
    )
