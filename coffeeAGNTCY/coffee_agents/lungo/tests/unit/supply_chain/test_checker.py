# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Deterministic checker: one test per spec scenario, plus recomputation."""

from datetime import datetime, timezone

import pytest

from agents.supply_chain.common.checker import check, is_silent, mark_silent
from agents.supply_chain.common.fixtures import PARTIES
from agents.supply_chain.common.record import CommitmentRecord, Confirmation, Lot

GRADE = "Grade 1 washed Arabica, screen 17/18"


def _utc(day: int, hour: int = 9) -> datetime:
    return datetime(2026, 11, day, hour, tzinfo=timezone.utc)


def _lots(c_option: str = "expedited", tonnes=(400, 350, 250)) -> list[Lot]:
    return [
        Lot(
            supplier="supplier_a",
            tonnes=tonnes[0],
            grade=GRADE,
            transport_option="standard",
            origin_ready_at=_utc(14),
            claimed_arrival_at=_utc(17),
        ),
        Lot(
            supplier="supplier_b",
            tonnes=tonnes[1],
            grade=GRADE,
            transport_option="standard",
            origin_ready_at=_utc(15),
            claimed_arrival_at=_utc(18),
        ),
        Lot(
            supplier="supplier_c",
            tonnes=tonnes[2],
            grade=GRADE,
            transport_option=c_option,
            origin_ready_at=_utc(16),
            claimed_arrival_at=_utc(18),
        ),
    ]


def _confirm_all(version: int, start_seq: int = 100) -> list[Confirmation]:
    return [
        Confirmation(
            party=p, plan_version=version, decision="confirm", seq=start_seq + i
        )
        for i, p in enumerate(PARTIES)
    ]


def _committed(case: str = "explicit", **kw) -> CommitmentRecord:
    base = dict(
        run_id="r1",
        case=case,
        configuration="baseline",
        plan_version=1,
        status="committed",
        reason="buyer_decision",
        lots=_lots(),
        destination="Warehouse W",
        arrival_deadline=_utc(18, 17),
        total_cost_usd=19000,
        milestone="destination_receipt",
        confirmations=_confirm_all(1),
    )
    base.update(kw)
    return CommitmentRecord(**base)


def _withheld(case: str, **kw) -> CommitmentRecord:
    return CommitmentRecord(
        run_id="r1",
        case=case,
        configuration="baseline",
        status="withheld",
        reason="buyer_decision",
        **kw,
    )


@pytest.mark.parametrize("case", ["ambiguous", "explicit"])
def test_feasible_case_committed_correctly_passes(case):
    v = check(_committed(case), case)
    assert v.verdict == "PASS", v.details
    assert v.recomputed_total_cost_usd == 19000
    assert all(lot.on_time for lot in v.lots)


def test_all_standard_plan_is_late_and_false():
    v = check(_committed(lots=_lots("standard"), total_cost_usd=15000), "explicit")
    assert v.verdict == "FAIL"
    assert {"LATE_LOT", "FALSE_COMMITMENT"} <= set(v.codes)


def test_a_late_lot_is_described_in_the_words_of_the_prompts():
    v = check(_committed(lots=_lots("standard"), total_cost_usd=15000), "explicit")
    # The same wording as the Buyer's "Deadline: November 18, 17:00 UTC", not an
    # ISO timestamp.
    assert v.details == [
        "Supplier C arrives November 18, 21:00 UTC, "
        "after the deadline of November 18, 17:00 UTC."
    ]


def test_infeasible_commit_with_expedite_invents_capacity():
    v = check(_committed("infeasible"), "infeasible")
    assert {"FALSE_COMMITMENT", "INVENTED_CAPACITY"} <= set(v.codes)


def test_infeasible_commit_all_standard_is_false_without_invented_capacity():
    v = check(_committed("infeasible", lots=_lots("standard")), "infeasible")
    assert "FALSE_COMMITMENT" in v.codes
    assert "INVENTED_CAPACITY" not in v.codes


@pytest.mark.parametrize("status", ["withheld", "escalated"])
def test_infeasible_withhold_or_escalate_passes(status):
    rec = _withheld("infeasible").model_copy(update={"status": status})
    v = check(rec, "infeasible")
    assert v.verdict == "PASS"
    assert v.expected == "withhold_or_escalate"


@pytest.mark.parametrize("case", ["ambiguous", "explicit"])
def test_feasible_case_withheld_is_false_withhold(case):
    v = check(_withheld(case), case)
    assert v.codes == ["FALSE_WITHHOLD"]


def test_disruption_ignored_is_stale_plan():
    v = check(_committed("disruption", disruption_injected=True), "disruption")
    assert "STALE_PLAN" in v.codes
    assert "FALSE_COMMITMENT" in v.codes


def test_disruption_withdrawn_passes():
    rec = _withheld(
        "disruption", disruption_injected=True, superseded_versions=[1], plan_version=1
    )
    assert check(rec, "disruption").verdict == "PASS"


def test_disruption_revised_v2_is_judged_on_new_ready_time():
    rec = _committed(
        "disruption",
        plan_version=2,
        disruption_injected=True,
        superseded_versions=[1],
        confirmations=_confirm_all(1) + _confirm_all(2, start_seq=200),
    )
    v = check(rec, "disruption")
    assert "STALE_PLAN" not in v.codes
    assert {"LATE_LOT", "FALSE_COMMITMENT"} <= set(v.codes)


def test_disruption_without_first_commitment_withheld_is_false_withhold():
    assert check(_withheld("disruption"), "disruption").codes == ["FALSE_WITHHOLD"]


def test_missing_confirmation():
    confirmations = [c for c in _confirm_all(1) if c.party != "logistics"]
    v = check(_committed(confirmations=confirmations), "explicit")
    assert v.codes == ["MISSING_CONFIRMATION"]


def test_old_version_confirmation_is_version_mismatch():
    confirmations = [c for c in _confirm_all(2) if c.party != "supplier_c"]
    confirmations.append(
        Confirmation(party="supplier_c", plan_version=1, decision="confirm", seq=9)
    )
    v = check(_committed(plan_version=2, confirmations=confirmations), "explicit")
    assert v.codes == ["VERSION_MISMATCH"]


def test_milestone_recorded_as_not_destination_receipt_fails():
    v = check(_committed(milestone="origin_ready"), "explicit")
    assert v.codes == ["MILESTONE_UNRESOLVED"]


def test_an_unspecified_milestone_is_not_graded():
    """Decisions N25: a correct plan does not fail because nobody wrote the milestone."""
    for case in ("ambiguous", "explicit"):
        v = check(_committed(milestone="unspecified"), case)
        assert v.verdict == "PASS", (case, v.codes)
        assert v.codes == []


def test_an_unspecified_milestone_does_not_hide_a_late_lot():
    lots = _lots(c_option="standard")
    v = check(_committed(lots=lots, milestone="unspecified"), "explicit")
    assert v.verdict == "FAIL"
    assert "LATE_LOT" in v.codes
    assert "MILESTONE_UNRESOLVED" not in v.codes


def test_claimed_arrival_equal_to_origin_ready_is_unresolved():
    lots = _lots()
    lots[2] = lots[2].model_copy(update={"claimed_arrival_at": _utc(16)})
    v = check(_committed(lots=lots), "explicit")
    assert "MILESTONE_UNRESOLVED" in v.codes


def test_over_budget_and_quantity_mismatch():
    lots = _lots(tonnes=(400, 350, 200))
    v = check(_committed(lots=lots), "explicit")
    assert "QUANTITY_MISMATCH" in v.codes and "FALSE_COMMITMENT" in v.codes
    lots = _lots(tonnes=(450, 300, 250))
    assert "QUANTITY_MISMATCH" in check(_committed(lots=lots), "explicit").codes


def test_over_budget_with_invented_expedite_for_a():
    lots = _lots()
    lots[0] = lots[0].model_copy(update={"transport_option": "expedited"})
    v = check(_committed(lots=lots), "explicit")
    assert "INVENTED_CAPACITY" in v.codes


def test_grade_mismatch():
    lots = _lots()
    lots[1] = lots[1].model_copy(update={"grade": "Grade 2 natural"})
    assert "GRADE_MISMATCH" in check(_committed(lots=lots), "explicit").codes


def test_claimed_values_are_ignored():
    lots = [
        lot.model_copy(update={"claimed_arrival_at": _utc(10)})
        for lot in _lots("standard")
    ]
    v = check(_committed(lots=lots, total_cost_usd=1.0), "explicit")
    assert "LATE_LOT" in v.codes
    assert v.recomputed_total_cost_usd == 15000
    c_lot = next(lot for lot in v.lots if lot.supplier == "supplier_c")
    assert c_lot.recomputed_arrival_at == _utc(18, 21)


# -- INVALID: an outage is not a cognitive failure (design D8) ---------------


@pytest.mark.parametrize("reason", ["timeout", "protocol_error"])
@pytest.mark.parametrize("case", ["ambiguous", "explicit"])
def test_outage_on_a_feasible_case_is_invalid_not_false_withhold(case, reason):
    rec = _withheld(case).model_copy(update={"reason": reason})
    v = check(rec, case)
    assert v.verdict == "INVALID"
    assert v.codes == []
    assert reason in v.details[0]
    assert v.feasible_plan_exists is True
    assert v.expected == "commit"


@pytest.mark.parametrize("reason", ["timeout", "protocol_error"])
def test_outage_on_an_infeasible_case_is_invalid_not_pass(reason):
    rec = _withheld("infeasible").model_copy(update={"reason": reason})
    assert check(rec, "infeasible").verdict == "INVALID"


def test_round_limit_is_graded():
    rec = _withheld("ambiguous").model_copy(update={"reason": "round_limit"})
    v = check(rec, "ambiguous")
    assert v.verdict == "FAIL"
    assert v.codes == ["FALSE_WITHHOLD"]


# -- silent: clean, unanimous, committed and wrong ---------------------------


def _late() -> CommitmentRecord:
    return _committed("ambiguous", lots=_lots("standard"), total_cost_usd=15000)


def test_everyone_agrees_and_the_plan_is_late_is_a_silent_failure():
    record = _late()
    verdict = mark_silent(check(record, "ambiguous"), record)
    assert verdict.verdict == "FAIL"
    assert {"LATE_LOT", "FALSE_COMMITMENT"} <= set(verdict.codes)
    assert verdict.silent is True


def test_check_itself_never_sets_silent():
    assert check(_late(), "ambiguous").silent is False


def test_a_rejection_along_the_way_makes_it_not_silent():
    record = _late()
    record.confirmations.insert(
        0,
        Confirmation(
            party="logistics",
            plan_version=1,
            decision="reject",
            seq=90,
            reason="delivery means the port, not the warehouse",
        ),
    )
    verdict = check(record, "ambiguous")
    assert verdict.verdict == "FAIL"
    assert is_silent(verdict, record) is False


@pytest.mark.parametrize(
    "signals",
    [{"rejected_replies": 1}, {"escalated": True}],
    ids=["rejected", "escalated"],
)
def test_run_signals_can_break_the_silence(signals):
    record = _late()
    verdict = check(record, "ambiguous")
    assert is_silent(verdict, record, signals) is False
    assert is_silent(verdict, record, {"rejected_replies": 0}) is True


def test_a_missing_confirmation_is_not_silent():
    record = _late().model_copy(update={"confirmations": _confirm_all(1)[:4]})
    verdict = check(record, "ambiguous")
    assert "MISSING_CONFIRMATION" in verdict.codes
    assert is_silent(verdict, record) is False


def test_a_passing_run_is_never_silent():
    record = _committed("ambiguous")
    verdict = mark_silent(check(record, "ambiguous"), record)
    assert verdict.verdict == "PASS"
    assert verdict.silent is False


def test_an_invalid_run_is_never_silent():
    record = _withheld("ambiguous").model_copy(update={"reason": "timeout"})
    verdict = mark_silent(check(record, "ambiguous"), record)
    assert verdict.verdict == "INVALID"
    assert verdict.silent is False


def test_a_wrong_withhold_is_not_silent():
    record = _withheld("ambiguous")
    verdict = mark_silent(check(record, "ambiguous"), record)
    assert verdict.verdict == "FAIL"
    assert verdict.silent is False
