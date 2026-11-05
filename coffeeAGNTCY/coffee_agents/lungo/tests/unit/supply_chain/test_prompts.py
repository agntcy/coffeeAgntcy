# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Spec: five agents with separate information. No role sees others' figures."""

import pytest

from agents.supply_chain.common import fixtures as f
from agents.supply_chain.common.prompts import (
    buyer_prompt,
    logistics_prompt,
    supplier_prompt,
)

TRANSPORT_FIGURES = (
    "15,000",
    "19,000",
    "60 hours",
    "3 days",
    "2 days",
    "72",
    "60",
    "48",
    "xpedite",
    "capacity",
)
SUPPLIER_FIGURES = (
    "400",
    "350",
    "250",
    "November 14",
    "November 15",
    "November 16",
    "November 17",
)
BUYER_FIGURES = ("20,000", "1,000", "17:00", "November 18", "budget")


@pytest.mark.parametrize("case", f.CASES)
def test_suppliers_see_no_transport_or_buyer_figures(case):
    for sid in f.SUPPLIERS:
        text = supplier_prompt(f.supplier_slice(sid, case))
        for figure in TRANSPORT_FIGURES + BUYER_FIGURES:
            assert figure not in text, (sid, figure)


@pytest.mark.parametrize("case", f.CASES)
def test_each_supplier_sees_only_its_own_lot(case):
    own = {"supplier_a": "400", "supplier_b": "350", "supplier_c": "250"}
    for sid, qty in own.items():
        text = supplier_prompt(f.supplier_slice(sid, case))
        assert qty in text
        assert all(other not in text for o, other in own.items() if o != sid)


@pytest.mark.parametrize("case", f.CASES)
def test_buyer_sees_no_supplier_or_transport_figures(case):
    text = buyer_prompt(f.buyer_slice(case))
    for figure in TRANSPORT_FIGURES + SUPPLIER_FIGURES:
        assert figure not in text, figure


@pytest.mark.parametrize("case", f.CASES)
def test_logistics_sees_no_budget_deadline_or_supplier_terms(case):
    text = logistics_prompt(f.logistics_slice(case))
    for figure in BUYER_FIGURES + SUPPLIER_FIGURES:
        assert figure not in text, figure


def test_logistics_infeasible_does_not_say_expedited_capacity_is_missing():
    """Decisions N41: the carrier holds no record, so it cannot be told "none"."""
    text = logistics_prompt(f.logistics_slice("infeasible"))
    assert "no capacity is available" not in text
    assert "Its capacity must be explicitly confirmed by you." in text
    assert "You hold no capacity record to check it against." in text
    assert "19,000" in text
    assert "say when each lot would arrive at Warehouse W" in text


def test_logistics_in_the_other_cases_keeps_its_old_prompt():
    for case in ("ambiguous", "explicit", "disruption"):
        text = logistics_prompt(f.logistics_slice(case))
        assert "no capacity record" not in text
        assert "19,000" in text
    # Only ambiguous (decisions N43) and infeasible quote arrival times.
    for case in ("explicit", "disruption"):
        assert "say when each lot would arrive" not in logistics_prompt(
            f.logistics_slice(case)
        )
    assert "say when each lot would arrive" in logistics_prompt(
        f.logistics_slice("ambiguous")
    )


def test_supplier_c_in_ambiguous_states_its_own_clock_and_the_others_utc():
    """Decisions N42 and N44: a wall time, and the offset is not in C's words."""
    c = supplier_prompt(f.supplier_slice("supplier_c", "ambiguous"))
    assert "November 16, 09:00 local time at Origin facility C" in c
    assert "UTC-5" not in c and "14:00" not in c and "behind UTC" not in c
    a = supplier_prompt(f.supplier_slice("supplier_a", "ambiguous"))
    assert "November 14, 09:00 UTC" in a
    shared = supplier_prompt(f.supplier_slice("supplier_c", "explicit"))
    assert "November 16, 09:00 UTC" in shared


def test_no_party_is_told_the_facility_offset():
    """Decisions N45: the five hours stay in the fixture, not in a prompt."""
    for case in f.CASES:
        assert "civil time" not in buyer_prompt(f.buyer_slice(case))
        assert "behind UTC" not in buyer_prompt(f.buyer_slice(case))
        assert "UTC-5" not in logistics_prompt(f.logistics_slice(case))
        for sid in f.SUPPLIERS:
            assert "behind UTC" not in supplier_prompt(f.supplier_slice(sid, case))


@pytest.mark.parametrize("case", f.CASES)
def test_no_prompt_states_the_answer(case):
    texts = [
        buyer_prompt(f.buyer_slice(case)),
        logistics_prompt(f.logistics_slice(case)),
    ]
    texts += [supplier_prompt(f.supplier_slice(s, case)) for s in f.SUPPLIERS]
    for text in texts:
        assert "November 18, 09:00" not in text
        assert "expedite Supplier C" not in text.lower()


def test_buyer_states_its_timing_only_in_its_own_opening_words():
    """Prompt version 2 (decisions N25): no milestone is defined for the Buyer."""
    ambiguous = buyer_prompt(f.buyer_slice("ambiguous"))
    assert f.buyer_slice("ambiguous").opening_wording in ambiguous
    assert "received at" not in ambiguous
    assert "means" not in ambiguous
    assert "November 18, 22:00 UTC" in ambiguous  # the deadline time, not a milestone
    # A case whose wording names the milestone still gives the Buyer that wording.
    explicit = buyer_prompt(f.buyer_slice("explicit"))
    assert "arrival at Warehouse W by November 18." in explicit
    assert "November 18, 17:00 UTC" in explicit  # the time is in the brief only


def test_the_buyer_holds_its_own_deadline_time():
    """Decisions N40 and N42: 22:00 for disruption and ambiguous, else 17:00."""
    for case in ("ambiguous", "disruption"):
        assert "Deadline: November 18, 22:00 UTC" in buyer_prompt(f.buyer_slice(case))
    for case in ("explicit", "infeasible"):
        assert "Deadline: November 18, 17:00 UTC" in buyer_prompt(f.buyer_slice(case))


def test_the_infeasible_opening_names_the_deadline_time():
    """Decisions N43: every party sees that standard transport is late."""
    wording = f.buyer_slice("infeasible").opening_wording
    assert "arrival at Warehouse W by November 18, 17:00 UTC." in wording


@pytest.mark.parametrize("case", ["explicit", "disruption"])
def test_the_deadline_time_is_not_in_the_opening_words_of_the_named_milestone_cases(
    case,
):
    """Prompt version 9 (decisions N27): the time of day is the Buyer's alone."""
    wording = f.buyer_slice(case).opening_wording
    assert "arrival at Warehouse W by November 18." in wording
    assert "17:00" not in wording
    assert "17:00" not in logistics_prompt(f.logistics_slice(case))
