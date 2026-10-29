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


def test_logistics_infeasible_has_no_expedite_price():
    text = logistics_prompt(f.logistics_slice("infeasible"))
    assert "19,000" not in text
    assert "no capacity is available" in text
    assert "19,000" in logistics_prompt(f.logistics_slice("explicit"))


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
    assert "November 18, 17:00 UTC" in ambiguous  # the deadline time, not a milestone
    # A case whose wording names the milestone still gives the Buyer that wording.
    explicit = buyer_prompt(f.buyer_slice("explicit"))
    assert "arrival at Warehouse W by November 18." in explicit
    assert "November 18, 17:00 UTC" in explicit  # the time is in the brief only


@pytest.mark.parametrize("case", ["explicit", "infeasible", "disruption"])
def test_the_deadline_time_is_not_in_the_opening_words_of_the_named_milestone_cases(
    case,
):
    """Prompt version 9 (decisions N27): the time of day is the Buyer's alone."""
    wording = f.buyer_slice(case).opening_wording
    assert "arrival at Warehouse W by November 18." in wording
    assert "17:00" not in wording
    assert "17:00" not in logistics_prompt(f.logistics_slice(case))
