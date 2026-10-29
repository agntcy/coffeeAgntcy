# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Fixture numbers match the use case, and slices hold only their own party."""

from datetime import datetime, timezone

import pytest

from agents.supply_chain.common import fixtures as f
from agents.supply_chain.common.checker import feasible_plan_exists


def _utc(day: int, hour: int = 9) -> datetime:
    return datetime(2026, 11, day, hour, tzinfo=timezone.utc)


def test_use_case_numbers():
    s = f.load_scenario()
    assert s.simulated is True
    assert {k: v.quantity_t for k, v in s.suppliers.items()} == {
        "supplier_a": 400,
        "supplier_b": 350,
        "supplier_c": 250,
    }
    assert {k: v.ready_at for k, v in s.suppliers.items()} == {
        "supplier_a": _utc(14),
        "supplier_b": _utc(15),
        "supplier_c": _utc(16),
    }
    assert s.buyer.quantity_t == 1000
    assert s.buyer.deadline == _utc(18, 17)
    assert s.buyer.budget_usd == 20000


def test_transport_totals_and_expedite():
    w = f.world("explicit")
    standard, expedited = w.option("standard"), w.option("expedited")
    assert standard.transit_hours == 60
    assert sum(standard.lot_cost_usd.values()) == 15000
    assert expedited.transit_hours == 48
    assert set(expedited.lot_cost_usd) == {"supplier_c"}
    with_c_expedited = (
        standard.lot_cost_usd["supplier_a"]
        + standard.lot_cost_usd["supplier_b"]
        + expedited.lot_cost_usd["supplier_c"]
    )
    assert with_c_expedited == 19000
    assert w.arrival("supplier_c", expedited) == _utc(18)
    assert w.arrival("supplier_c", standard) == _utc(18, 21)


@pytest.mark.parametrize(
    ("case", "disrupted", "feasible"),
    [
        ("ambiguous", False, True),
        ("explicit", False, True),
        ("infeasible", False, False),
        ("disruption", False, True),
        ("disruption", True, False),
    ],
)
def test_expected_feasibility(case, disrupted, feasible):
    assert feasible_plan_exists(f.world(case, disrupted=disrupted)) is feasible


def test_infeasible_case_disables_expedite_only():
    lg = f.logistics_slice("infeasible").logistics
    assert {o.id: o.available for o in lg.options} == {
        "standard": True,
        "expedited": False,
    }


def test_disruption_moves_supplier_c_only_when_injected():
    assert f.supplier_slice("supplier_c", "disruption").supplier.ready_at == _utc(16)
    moved = f.supplier_slice("supplier_c", "disruption", disrupted=True)
    assert moved.supplier.ready_at == _utc(17)
    assert f.supplier_slice(
        "supplier_b", "disruption", disrupted=True
    ).supplier.ready_at == _utc(15)


def test_ambiguous_wording_names_no_milestone():
    wording = f.buyer_slice("ambiguous").opening_wording
    assert "delivered by November 18" in wording
    assert "Warehouse W" not in wording and "17:00" not in wording
    assert "arrival at Warehouse W" in f.buyer_slice("explicit").opening_wording


@pytest.mark.parametrize("case", f.CASES)
def test_slices_hold_only_their_own_party(case):
    buyer = f.buyer_slice(case).model_dump()
    assert set(buyer) == {"case", "buyer", "opening_wording"}
    for sid in f.SUPPLIERS:
        sl = f.supplier_slice(sid, case).model_dump()
        assert set(sl) == {"case", "supplier_id", "supplier"}
        assert "transit_hours" not in str(sl) and "budget" not in str(sl)
    lg = f.logistics_slice(case).model_dump()
    assert set(lg) == {"case", "logistics"}
    assert (
        "ready_at" not in str(lg)
        and "budget" not in str(lg)
        and "quantity" not in str(lg)
    )
