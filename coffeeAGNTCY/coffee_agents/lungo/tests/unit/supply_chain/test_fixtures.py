# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Fixture numbers match the use case, and slices hold only their own party."""

from datetime import datetime, timedelta, timezone

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


def test_only_ambiguous_and_disruption_have_their_own_deadline():
    """22:00 there, the shared 17:00 everywhere else."""
    for case in ("ambiguous", "disruption"):
        assert f.buyer_slice(case).buyer.deadline == _utc(18, 22)
        assert f.world(case).buyer.deadline == _utc(18, 22)
    for case in ("explicit", "infeasible"):
        assert f.buyer_slice(case).buyer.deadline == _utc(18, 17)
        assert f.world(case).buyer.deadline == _utc(18, 17)


def test_disruption_all_standard_is_on_time_before_the_delay_and_late_after():
    before, after = f.world("disruption"), f.world("disruption", disrupted=True)
    standard = before.option("standard")
    assert all(
        before.arrival(s, standard) <= before.buyer.deadline for s in f.SUPPLIERS
    )
    # After the delay only Supplier C moves, and no option gets it there on time.
    assert after.arrival("supplier_a", standard) <= after.buyer.deadline
    assert after.arrival("supplier_b", standard) <= after.buyer.deadline
    for option in (standard, after.option("expedited")):
        assert after.arrival("supplier_c", option) > after.buyer.deadline


def test_ambiguous_supplier_c_works_on_a_clock_five_hours_behind_utc():
    """09:00 local is 14:00 UTC; the others are unchanged."""
    c = f.supplier_slice("supplier_c", "ambiguous").supplier
    assert c.utc_offset_hours == -5
    assert c.ready_at == _utc(16, 14)
    for sid, day in (("supplier_a", 14), ("supplier_b", 15)):
        other = f.supplier_slice(sid, "ambiguous").supplier
        assert other.utc_offset_hours == 0 and other.ready_at == _utc(day)
    for case in ("explicit", "infeasible", "disruption"):
        shared = f.supplier_slice("supplier_c", case).supplier
        assert shared.utc_offset_hours == 0 and shared.ready_at == _utc(16)


def test_ambiguous_standard_looks_on_time_in_utc_but_is_late():
    w = f.world("ambiguous")
    standard, expedited = w.option("standard"), w.option("expedited")
    c = w.suppliers["supplier_c"]
    # Read as if 09:00 were UTC: Nov 18, 21:00, before the 22:00 deadline.
    naive = _utc(16, 9) + timedelta(hours=standard.transit_hours)
    assert naive == _utc(18, 21) and naive <= w.buyer.deadline
    # The true arrival is Nov 19, 02:00, after it. Expedited is on time.
    assert w.arrival("supplier_c", standard) == _utc(19, 2) > w.buyer.deadline
    assert w.arrival("supplier_c", expedited) == _utc(18, 14) <= w.buyer.deadline
    assert c.ready_at == _utc(16, 14)


def test_infeasible_expedited_capacity_is_a_fact_nobody_holds():
    """The truth is "no capacity", but Logistics has no record."""
    lg = f.logistics_slice("infeasible").logistics
    expedited = next(o for o in lg.options if o.id == "expedited")
    assert expedited.available is False and expedited.capacity_known is False
    assert lg.quotes_arrival is True
    # Ambiguous quotes arrival times too, but only infeasible
    # lacks a capacity record.
    assert f.logistics_slice("ambiguous").logistics.quotes_arrival is True
    for case in ("ambiguous", "explicit", "disruption"):
        other = f.logistics_slice(case).logistics
        assert all(o.capacity_known for o in other.options)
    for case in ("explicit", "disruption"):
        assert f.logistics_slice(case).logistics.quotes_arrival is False


def test_ambiguous_wording_names_no_milestone():
    wording = f.buyer_slice("ambiguous").opening_wording
    assert "delivered by November 18" in wording
    assert "Warehouse W" not in wording and "17:00" not in wording
    assert "arrival at Warehouse W" in f.buyer_slice("explicit").opening_wording


@pytest.mark.parametrize("case", f.CASES)
def test_slices_hold_only_their_own_party(case):
    buyer = f.buyer_slice(case).model_dump()
    assert set(buyer) == {"case", "buyer", "opening_wording", "facility_clocks"}
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


def _logistics(*options: tuple[str, str]) -> dict:
    return {
        "organization": "Carrier",
        "destination": "Warehouse W",
        "options": [
            {
                "id": option_id,
                "description": description,
                "transit_hours": 60,
                "lot_cost_usd": {"supplier_a": 5000},
                "available": True,
                "requires_capacity_confirmation": False,
            }
            for option_id, description in options
        ],
    }


@pytest.mark.parametrize(
    "options",
    [
        [("standard", "Standard road transport"), ("standard", "Road freight")],
        [("standard", "Road transport"), ("slow", "road-transport")],
        [("standard", "Standard road transport"), ("slow", "Standard")],
    ],
    ids=["same id", "same description", "description reads as another id"],
)
def test_option_names_must_be_unique(options):
    with pytest.raises(ValueError, match="duplicate transport option id|share"):
        f.LogisticsData.model_validate(_logistics(*options))


def test_shipped_options_are_unique():
    f.LogisticsData.model_validate(f.load_scenario().logistics.model_dump())


def test_a_duplicate_key_in_the_scenario_file_is_rejected(tmp_path):
    text = f.SCENARIO_PATH.read_text(encoding="utf-8")
    duplicated = text.replace('"suppliers": {', '"suppliers": {"supplier_a": {}, ', 1)
    path = tmp_path / "scenario.json"
    path.write_text(duplicated, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate keys.*supplier_a"):
        f.load_scenario(path)
