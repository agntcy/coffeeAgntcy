# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Record builder: copies the plan and the received confirmations, nothing more."""

from types import SimpleNamespace

import pytest

from agents.supervisors.supply_chain import record_builder
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
        ("standard-road-transport", "standard"),
        ("Standard road transport (60 hours)", "standard"),
        ("Standard road transport via Meridian Freight", "standard"),
        ("  EXPEDITED  ", "expedited"),
        ("Expedited transport", "expedited"),
        ("expedited freight", "expedited"),
        ("Expedited transport for supplier_c", "expedited"),
        # Real Buyer wordings from baseline runs.
        ("Standard delivery", "standard"),
        ("Standard 60-hour transit", "standard"),
        ("Standard Road, 60h delivery", "standard"),
        ("Standard Logistics, 60 hours delivery via Meridian Freight.", "standard"),
        ("Expedited delivery", "expedited"),
        ("expedited transport for 48-hour delivery", "expedited"),
        ("Expedited Transport (for Supplier C only)", "expedited"),
        ("Expedited Transport (for Supplier C lot only)", "expedited"),
        ("Expedited transport (optional for Supplier C)", "expedited"),
        # Names no option.
        ("express air freight", "express air freight"),
        ("Meridian Freight", "Meridian Freight"),
        ("substandard", "substandard"),
        ("", ""),
        # Names more than one option.
        ("Expedited (upgrade from standard)", "Expedited (upgrade from standard)"),
        ("standard or expedited", "standard or expedited"),
        ("Expedited standard", "Expedited standard"),
        # Rules an option out: never mapped to the option it rejects.
        ("not standard", "not standard"),
        ("Non-standard transport", "Non-standard transport"),
        ("Standard is unavailable", "Standard is unavailable"),
        ("Standard is out", "Standard is out"),
        (
            "Standard road transport is not feasible",
            "Standard road transport is not feasible",
        ),
        (
            "Standard road transport (not available)",
            "Standard road transport (not available)",
        ),
        (
            "Standard road transport fell through",
            "Standard road transport fell through",
        ),
        (
            "Standard road transport, not expedited",
            "Standard road transport, not expedited",
        ),
        # Extra prose is kept too: a visible false flag, not a silent mapping.
        (
            "Standard road transport (the cheaper option)",
            "Standard road transport (the cheaper option)",
        ),
        ("Standard road transport, no delays", "Standard road transport, no delays"),
    ],
)
def test_option_names_map_to_fixture_ids_and_unknown_names_are_kept(written, expected):
    assert normalize_option(written) == expected


def test_a_multi_word_option_id_is_matched(monkeypatch):
    option = SimpleNamespace(id="air freight", description="Air freight service")
    scenario = SimpleNamespace(
        logistics=SimpleNamespace(
            organization="Meridian Freight", destination="Warehouse W", options=[option]
        ),
        suppliers={},
    )
    monkeypatch.setattr(record_builder.fx, "load_scenario", lambda: scenario)
    assert normalize_option("Air freight, 2 hours") == "air freight"


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
