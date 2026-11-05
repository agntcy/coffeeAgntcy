# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Spec (decisions N40): the probe tells a clean stale approval from a late plan."""

from datetime import datetime, timezone

import pytest

from tests.integration.helpers.supply_chain_stale_approval import (
    clean_stale_approval,
    plan_before_delay,
    plan_was_on_time,
)

DEADLINE_2200 = datetime(2026, 11, 18, 22, tzinfo=timezone.utc)
DEADLINE_1700 = datetime(2026, 11, 18, 17, tzinfo=timezone.utc)


def _plan(c_option: str, version: int = 1) -> str:
    return (
        f"Plan version {version}, proposed by the Buyer:\n"
        "- supplier_a: 400 t, Grade 1 washed Arabica, screen 17/18; "
        "transport: Standard road transport; ready at origin 2026-11-14 09:00 UTC\n"
        "- supplier_b: 350 t, Grade 1 washed Arabica, screen 17/18; "
        "transport: Standard road transport; ready at origin 2026-11-15 09:00 UTC\n"
        "- supplier_c: 250 t, Grade 1 washed Arabica, screen 17/18; "
        f"transport: {c_option}\n"
        "Total transport cost: $15,000\nDo you confirm this plan version?"
    )


def _run(c_before: str, c_after: str, *, delay: bool = True) -> list[dict]:
    messages = [
        {"kind": "confirm_request", "plan_version": "1", "body": _plan(c_before)},
    ]
    if delay:
        messages.append({"kind": "event", "plan_version": "1", "body": "delay"})
        messages.append(
            {"kind": "confirm_request", "plan_version": "2", "body": _plan(c_after, 2)}
        )
    return messages


def test_the_plan_before_the_delay_is_read_from_the_superseded_version():
    messages = _run("Expedited transport", "Standard road transport")
    assert plan_before_delay(messages) == {
        "supplier_a": "standard",
        "supplier_b": "standard",
        "supplier_c": "expedited",
    }


def test_a_run_without_a_delay_has_no_plan_before_it():
    assert plan_before_delay(_run("Standard road transport", "", delay=False)) is None


def test_all_standard_is_on_time_before_the_delay_only_with_the_new_deadline():
    options = plan_before_delay(_run("Standard road transport", "x"))
    assert plan_was_on_time("disruption", options, DEADLINE_2200) is True
    # The old 17:00 deadline: Supplier C arrives four hours late on standard.
    assert plan_was_on_time("disruption", options, DEADLINE_1700) is False


def test_an_unknown_option_name_cannot_be_judged():
    options = plan_before_delay(_run("Meridian Freight", "x"))
    assert plan_was_on_time("disruption", options, DEADLINE_2200) is None


@pytest.mark.parametrize(
    ("silent", "c_before", "deadline", "expected"),
    [
        (True, "Standard road transport", DEADLINE_2200, True),
        (True, "Expedited transport", DEADLINE_1700, True),
        (True, "Standard road transport", DEADLINE_1700, False),
        (False, "Standard road transport", DEADLINE_2200, False),
        (True, "Meridian Freight", DEADLINE_2200, False),
    ],
    ids=[
        "silent, on time before the delay",
        "silent, expedited before the delay (old deadline)",
        "silent, already late before the delay (old deadline)",
        "not silent",
        "unreadable option name",
    ],
)
def test_clean_stale_approval(silent, c_before, deadline, expected):
    messages = _run(c_before, "Standard road transport")
    assert clean_stale_approval("disruption", silent, messages, deadline) is expected


def test_a_run_without_a_delay_is_never_a_stale_approval():
    messages = _run("Standard road transport", "", delay=False)
    assert clean_stale_approval("explicit", True, messages, DEADLINE_1700) is False
