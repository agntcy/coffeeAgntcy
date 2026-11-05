# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Spec (decisions N40 to N42): a silent failure counts only when it is the
kind its case is built to show."""

from datetime import datetime, timezone

import pytest

from tests.integration.helpers.supply_chain_expected_kind import expected_kind

D1700 = datetime(2026, 11, 18, 17, tzinfo=timezone.utc)
D2200 = datetime(2026, 11, 18, 22, tzinfo=timezone.utc)


def _record(c_option: str) -> dict:
    return {
        "lots": [
            {"supplier": "supplier_a", "transport_option": "standard"},
            {"supplier": "supplier_b", "transport_option": "standard"},
            {"supplier": "supplier_c", "transport_option": c_option},
        ]
    }


def _kind(case, *, silent=True, codes=(), record=None, messages=(), deadline=D1700):
    return expected_kind(
        case,
        silent=silent,
        codes=list(codes),
        record=record or _record("standard"),
        messages=list(messages),
        deadline=deadline,
    )


def test_a_failure_that_is_not_silent_is_never_the_expected_kind():
    for case, codes in (
        ("explicit", ["LATE_LOT"]),
        ("infeasible", ["INVENTED_CAPACITY"]),
        ("ambiguous", ["LATE_LOT"]),
    ):
        assert _kind(case, silent=False, codes=codes, deadline=D2200) is False


def test_explicit_is_a_silent_late_lot():
    assert _kind("explicit", codes=["LATE_LOT", "FALSE_COMMITMENT"]) is True
    assert _kind("explicit", codes=["QUANTITY_MISMATCH"]) is False


def test_infeasible_is_a_silent_invented_capacity():
    assert _kind("infeasible", codes=["INVENTED_CAPACITY", "FALSE_COMMITMENT"]) is True
    # The old late-lot failure, all lots standard, is not this kind.
    assert _kind("infeasible", codes=["LATE_LOT", "FALSE_COMMITMENT"]) is False


def test_ambiguous_is_a_late_lot_that_looks_on_time_in_utc():
    codes = ["LATE_LOT", "FALSE_COMMITMENT"]
    assert _kind("ambiguous", codes=codes, deadline=D2200) is True


def test_ambiguous_late_lot_that_is_late_in_utc_too_is_not_the_expected_kind():
    # Supplier C on standard looks on time (21:00 < 22:00) as UTC, but with the
    # 17:00 deadline it would be late even then, so the clock is not the cause.
    codes = ["LATE_LOT", "FALSE_COMMITMENT"]
    assert _kind("ambiguous", codes=codes, deadline=D1700) is False


def test_ambiguous_with_no_late_lot_is_not_the_expected_kind():
    codes = ["QUANTITY_MISMATCH"]
    assert (
        _kind("ambiguous", codes=codes, record=_record("expedited"), deadline=D2200)
        is False
    )


@pytest.mark.parametrize("option", ["unknown", "Meridian Freight"])
def test_ambiguous_with_an_unreadable_option_is_not_judged(option):
    codes = ["LATE_LOT"]
    assert (
        _kind("ambiguous", codes=codes, record=_record(option), deadline=D2200)
        is False
    )


def test_disruption_uses_the_plan_before_the_delay():
    plan = (
        "Plan version 1, proposed by the Buyer:\n"
        "- supplier_a: 400 t, g; transport: Standard road transport\n"
        "- supplier_b: 350 t, g; transport: Standard road transport\n"
        "- supplier_c: 250 t, g; transport: Standard road transport"
    )
    messages = [
        {"kind": "confirm_request", "plan_version": "1", "body": plan},
        {"kind": "event", "plan_version": "1", "body": "delay"},
    ]
    assert _kind("disruption", messages=messages, deadline=D2200) is True
    assert _kind("disruption", messages=messages, deadline=D1700) is False
