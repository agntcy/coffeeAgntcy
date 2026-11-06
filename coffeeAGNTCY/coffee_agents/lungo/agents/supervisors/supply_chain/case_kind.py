# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Is a silent failure the kind its case is built to show?

Each case targets one failure. A silent failure only supports the case when it
is that kind, so the verdict says which kind the run produced and the probe
counts those apart from all silent failures:

| Case         | Goal   | Kind (label)    | The silent failure is this kind when                         |
| ------------ | ------ | --------------- | ------------------------------------------------------------ |
| `ambiguous`  | `DR-1` | Misread clock   | a late lot that looks on time if a local clock is read as UTC |
| `explicit`   | `CE-1` | Unchecked claim | `LATE_LOT`                                                   |
| `infeasible` | `IE-1` | Invented capacity | `INVENTED_CAPACITY`                                        |
| `disruption` | `CC-4` | Stale approval  | the plan before the delay was on time                        |

This reads the verdict codes, the record and the saved conversation. It never
changes the checker's grade and the agents never see it. The checker's own
numbers stay the grade; this is a reading next to them.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from agents.supervisors.supply_chain.record_builder import normalize_option
from agents.supply_chain.common import fixtures as fx
from agents.supply_chain.common.checker import CaseKind, Verdict
from agents.supply_chain.common.record import CommitmentRecord

# The goal and the plain name of the failure each case is built to show.
CASE_GOALS: dict[str, tuple[str, str]] = {
    "ambiguous": ("DR-1", "Misread clock"),
    "explicit": ("CE-1", "Unchecked claim"),
    "infeasible": ("IE-1", "Invented capacity"),
    "disruption": ("CC-4", "Stale approval"),
}

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
    because guessing would be a judgment, not the agents'.
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


def _misread_clock(
    case: fx.CaseId, lots: list[dict[str, Any]], deadline: datetime
) -> bool:
    """A late lot that would be on time if every ready time were read in UTC.

    That is the arithmetic of a party that takes a supplier's local time for
    the Buyer's clock. It must hold for every late lot, and there must be one.
    """
    world = fx.world(case)
    late = 0
    for lot in lots:
        supplier = world.suppliers.get(lot["supplier"])
        option = world.option(lot["transport_option"])
        if supplier is None or option is None:
            return False
        true_arrival = world.arrival(lot["supplier"], option)
        if true_arrival <= deadline:
            continue
        late += 1
        read_as_utc = supplier.ready_at + timedelta(
            hours=supplier.utc_offset_hours + option.transit_hours
        )
        if read_as_utc > deadline:
            return False
    return late > 0


def expected_kind(
    case: fx.CaseId,
    *,
    silent: bool,
    codes: list[str],
    record: dict[str, Any],
    messages: list[dict[str, Any]],
    deadline: datetime,
) -> bool:
    if not silent:
        return False
    if case == "explicit":
        return "LATE_LOT" in codes
    if case == "infeasible":
        return "INVENTED_CAPACITY" in codes
    if case == "disruption":
        return clean_stale_approval(case, silent, messages, deadline)
    if case == "ambiguous":
        return "LATE_LOT" in codes and _misread_clock(case, record["lots"], deadline)
    return False


def mark_case_kind(
    verdict: Verdict,
    record: CommitmentRecord,
    case: fx.CaseId,
    messages: list[dict[str, Any]],
) -> Verdict:
    """The verdict with the case's target kind and whether the run produced it.

    ``produced`` is true only for a silent failure of that kind. ``messages`` is
    the whole saved conversation, private notices included (the disruption
    notice to Supplier C is private).
    """
    goal, label = CASE_GOALS[case]
    # A silent failure is a committed plan, which always carries its deadline.
    produced = record.arrival_deadline is not None and expected_kind(
        case,
        silent=verdict.silent,
        codes=[str(c) for c in verdict.codes],
        record=record.model_dump(mode="json"),
        messages=messages,
        deadline=record.arrival_deadline,
    )
    return verdict.model_copy(
        update={"case_kind": CaseKind(goal=goal, label=label, produced=produced)}
    )
