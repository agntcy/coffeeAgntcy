# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Record builder: copies the plan and the received confirmations, nothing more."""

import pytest

from agents.supervisors.supply_chain.outcome import Outcome, PlanLot, PlanProposal
from agents.supervisors.supply_chain.record_builder import (
    RunFacts,
    build_record,
    normalize_option,
)
from agents.supply_chain.common.envelope import Envelope
from agents.supply_chain.common.record import Confirmation


def _plan(option_c="Expedited transport") -> PlanProposal:
    return PlanProposal(
        lots=[
            PlanLot(
                supplier="supplier_a",
                tonnes=400,
                grade="G",
                transport_option="Standard road transport",
            ),
            PlanLot(
                supplier="supplier_b",
                tonnes=350,
                grade="G",
                transport_option="standard",
            ),
            PlanLot(
                supplier="supplier_c", tonnes=250, grade="G", transport_option=option_c
            ),
        ],
        total_cost_usd=19000,
        milestone="destination_receipt",
        milestone_definition="Received at Warehouse W.",
    )


def _msg(seq, sender, kind="negotiation"):
    return Envelope(
        run_id="r", seq=seq, sender=sender, to=("moderator",), kind=kind, body="x"
    )


@pytest.mark.parametrize(
    ("written", "expected"),
    [
        ("Standard road transport", "standard"),
        ("standard", "standard"),
        ("Standard", "standard"),
        ("Expedited transport", "expedited"),
        ("expedited freight", "expedited"),
        ("express air freight", "express air freight"),
    ],
)
def test_option_names_map_to_fixture_ids_and_unknown_names_are_kept(written, expected):
    assert normalize_option(written) == expected


def test_committed_outcome_copies_plan_confirmations_and_flags():
    confirmations = [
        Confirmation(party="buyer", plan_version=1, decision="confirm", seq=20)
    ]
    facts = RunFacts(
        run_id="r",
        case="explicit",
        configuration="baseline",
        confirmations=confirmations,
        disruption_injected=True,
        superseded_versions=[1],
        log=[
            _msg(2, "supplier_a"),
            _msg(3, "logistics"),
            _msg(4, "buyer"),
            _msg(5, "supplier_a", "confirm_reply"),
        ],
    )
    record = build_record(
        Outcome("committed", "buyer_decision", _plan(), plan_version=2), facts
    )

    assert (record.status, record.plan_version, record.total_cost_usd) == (
        "committed",
        2,
        19000,
    )
    assert [l.transport_option for l in record.lots] == [
        "standard",
        "standard",
        "expedited",
    ]
    assert record.lots[0].evidence_seq == [2]  # negotiation replies only
    assert record.evidence["transport"] == [3] and record.evidence[
        "buyer_requirement"
    ] == [4]
    assert record.confirmations == confirmations
    assert record.disruption_injected and record.superseded_versions == [1]
    # requirements come from the Buyer's own data, not from the plan
    assert record.destination == "Warehouse W" and record.arrival_deadline is not None


def test_withheld_outcome_has_no_lots_even_if_a_plan_was_proposed():
    facts = RunFacts(run_id="r", case="infeasible", configuration="baseline")
    record = build_record(
        Outcome("withheld", "party_rejected", _plan(), plan_version=1), facts
    )
    assert record.status == "withheld" and record.reason == "party_rejected"
    assert record.lots == [] and record.total_cost_usd is None


def test_committed_outcome_without_a_plan_is_rejected():
    with pytest.raises(ValueError, match="needs a plan"):
        Outcome("committed", "buyer_decision")
