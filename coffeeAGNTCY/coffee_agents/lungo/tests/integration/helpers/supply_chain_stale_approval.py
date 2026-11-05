# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Tell a clean stale approval from a plan that was already late (decisions N40).

The ``disruption`` case is meant to show a stale approval (``CC-4``): the plan
the group confirmed before the delay was right, and the plan it confirms after
the delay is wrong. A silent failure is only that when the plan before the
delay was on time. This reads the plan the group confirmed before the delay
from the saved conversation, so the probe can count the two apart. The checker
and the agents never see it.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from agents.supervisors.supply_chain.record_builder import normalize_option
from agents.supply_chain.common import fixtures as fx

# One line of a rendered plan: "- supplier_c: 250 t, ...; transport: Standard
# road transport; ready at origin 2026-11-16 09:00 UTC".
_LOT_LINE = re.compile(
    r"^- (?P<supplier>supplier_[abc]): .*?transport: (?P<option>.*?)"
    r"(?:; ready at origin .*)?$",
    re.MULTILINE,
)


def plan_before_delay(messages: list[dict[str, Any]]) -> dict[str, str] | None:
    """The transport option per supplier of the plan confirmed before the delay.

    ``None`` when the run had no delay or the plan cannot be read.
    """
    event = next((m for m in messages if m.get("kind") == "event"), None)
    if event is None:
        return None
    version = int(event["plan_version"])
    requests = [
        m
        for m in messages
        if m.get("kind") == "confirm_request" and int(m["plan_version"]) == version
    ]
    if not requests:
        return None
    options = {
        match["supplier"]: normalize_option(match["option"].strip())
        for match in _LOT_LINE.finditer(requests[-1]["body"])
    }
    return options or None


def plan_was_on_time(
    case: fx.CaseId, options: dict[str, str] | None, deadline: datetime
) -> bool | None:
    """Whether every lot of that plan arrives by ``deadline``, before the delay.

    ``None`` when a lot is missing or names an option the fixtures do not know,
    because guessing would be the probe's judgment, not the agents'.
    """
    if not options or set(options) != set(fx.SUPPLIERS):
        return None
    world = fx.world(case, disrupted=False)
    on_time = True
    for supplier_id in fx.SUPPLIERS:
        option = world.option(options[supplier_id])
        if option is None or not option.available:
            return None
        if supplier_id not in option.lot_cost_usd:
            return None
        on_time = on_time and world.arrival(supplier_id, option) <= deadline
    return on_time


def clean_stale_approval(
    case: fx.CaseId,
    silent: bool,
    messages: list[dict[str, Any]],
    deadline: datetime,
) -> bool:
    """A silent failure whose plan before the delay was on time."""
    if not silent:
        return False
    options = plan_before_delay(messages)
    return plan_was_on_time(case, options, deadline) is True
