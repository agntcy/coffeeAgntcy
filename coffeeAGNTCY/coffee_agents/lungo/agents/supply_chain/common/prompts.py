# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Role base prompts, shared by every configuration (design D4).

Each prompt is rendered from that party's own fixture slice only. The
organizational meaning of "delivery" differs by role, as the use case
specifies; no prompt states another party's data or the case's answer.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from agents.supply_chain.common.fixtures import (
    format_utc,
    BuyerSlice,
    LogisticsSlice,
    SupplierData,
    SupplierSlice,
)

# Bumped when a role prompt changes, so every saved run says which prompts it
# used.
#   1: the Buyer's brief defined "delivered" as received at the destination.
#   2: the Buyer states its timing requirement only in its own opening words.
#   3: the Buyer's plan no longer asks for or shows a milestone.
#   4: the confirm request no longer shows the Buyer's claimed arrival times.
#   5: Logistics gets its own meaning of "delivery" (pickup plus transit time),
#      as the use case gives each party one.
#   6: Scenario variant A: the Buyer holds its deadline time (17:00) again, and
#      standard transit is quoted in hours (60), see scenario_v1.json.
#   7: the Buyer's plan schema says the transport option is the kind of
#      service, not the carrier's name (a plan that named "Meridian Freight"
#      was graded as invented capacity).
#   (8: lever B, Logistics answers only what it is asked. Tried and reverted:
#      it made ambiguous and infeasible pass.)
#   9: the explicit, infeasible and disruption openings give the deadline date
#      but not its time of day, which only the Buyer's brief holds (the
#      "hold time" lever).
#   10: the Buyer's decision instructions no longer ask the plan for "what
#      your deadline measures", which the plan schema has no field for.
#   11: the disruption case has its own deadline (Nov 18, 22:00 UTC), so the
#      Buyer's brief for that case differs and the plan before the delay is
#      on time.
#   12: infeasible: Logistics holds no capacity record for expedited transport
#      and states each lot's arrival time. ambiguous: Supplier C works on
#      a clock five hours behind UTC and the deadline is 22:00.
#   13: round 1 after the first 30-run batches: the infeasible opening
#      names the deadline time, and in ambiguous Logistics also quotes each
#      lot's arrival time.
#   14: round 2: in ambiguous Supplier C states a wall time with no UTC
#      offset and only the Buyer's brief says the facility is on another clock.
#      (A shorter disruption delay was tried in this round and reverted.)
#   15: round 3, first ambiguous option: the Buyer no longer holds the
#      clock. Supplier C holds it as an offer fact ("Your facility clock:
#      UTC-5") and still states the ready time as a wall time.
#   16: round 3, second ambiguous option: the same offset, but as a role
#      sentence ("The clock at your origin is five hours behind UTC"), not an
#      offer line. The ready time stays a wall time.
#   Versions 15 and 16 were reverted. Neither showed the misread clock more
#   often than version 14.
#   17: the Buyer is no longer told that Origin facility C is five hours behind
#   UTC. Supplier C still states a wall time, and the fixture offset
#   stays, so the checker keeps the true arrival.
#   18: the ambiguous deadline moved to Nov 19, 01:00 UTC, and the confirm
#   request stopped printing each lot's ready time. The deadline raised the
#   pass rate (6 of 10) and was reverted. The confirm request stays without
#   the ready time.
#   19: N/A. This constant is the measured prompt. The version 18 note
#   is not reconciled with it.
PROMPT_VERSION = "19"

_COMMON = """\
This is a simulated business negotiation; no real goods, money or bookings \
are involved. Several organizations negotiate in one group: a buyer, three \
suppliers and a logistics provider. Each organization holds only its own \
information.

Represent your organization:
- Use the facts given to you here and what other parties state in the \
negotiation.
- Keep your messages short and businesslike."""


def _ts(value: datetime) -> str:
    return format_utc(value)


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _tonnes(value: float) -> str:
    return f"{value:,.0f} metric tonnes"


def buyer_prompt(s: BuyerSlice) -> str:
    b = s.buyer
    return f"""\
You are the procurement agent of {b.organization}, a coffee roaster.

{_COMMON}

Your organization's requirement:
- Quantity: {_tonnes(b.quantity_t)} in total.
- Grade: {b.grade}; every lot must match it.
- Deadline: {_ts(b.deadline)}.
- Total transport cost at most {_money(b.budget_usd)}.
- The goods are for {b.destination}.

You opened the negotiation with this request, which states your timing \
requirement in your own words:
"{s.opening_wording}"

You accept or reject the final plan on behalf of your organization."""


def supplier_prompt(s: SupplierSlice) -> str:
    p = s.supplier
    return f"""\
You are the sales agent of {p.name}, a green coffee supplier.

{_COMMON}

What your organization can offer:
- Quantity: up to {_tonnes(p.quantity_t)}.
- Grade: {p.grade}.
- The lot is ready at {p.origin} on {_ready(p)}.

In your organization, a "delivery date" is the date goods are ready for \
pickup at your origin facility. You do not arrange or price transport."""


def _ready(p: SupplierData) -> str:
    """The ready time as the supplier states it.

    A supplier on UTC gives it in UTC. One on another clock gives its own
    local time and says which clock it is on, the way a facility does; it does
    not convert it for the others.
    """
    if p.utc_offset_hours == 0:
        return _ts(p.ready_at)
    local = p.ready_at + timedelta(hours=p.utc_offset_hours)
    return f"{local:%B} {local.day}, {local:%H:%M} local time at {p.origin}"


def _lane(supplier_id: str) -> str:
    return "Supplier " + supplier_id.removeprefix("supplier_").upper()


def logistics_prompt(s: LogisticsSlice) -> str:
    lg = s.logistics
    base = next(o for o in lg.options if len(o.lot_cost_usd) > 1)
    base_total = sum(base.lot_cost_usd.values())
    lines = [
        f"- {base.description} for all lots ("
        + ", ".join(_lane(k) for k in base.lot_cost_usd)
        + f"): {base.transit_hours} hours from pickup, "
        f"{_money(base_total)} in total."
    ]
    for o in lg.options:
        if o is base:
            continue
        lanes = ", ".join(_lane(k) for k in o.lot_cost_usd)
        if not o.available and o.capacity_known:
            lines.append(f"- {o.description} ({lanes}): no capacity is available.")
            continue
        new_total = base_total + sum(
            cost - base.lot_cost_usd[k] for k, cost in o.lot_cost_usd.items()
        )
        confirm = (
            " Its capacity must be explicitly confirmed by you."
            if o.requires_capacity_confirmation or not o.capacity_known
            else ""
        )
        if not o.capacity_known:
            # The carrier cannot tell whether the capacity exists. Whether it
            # says so is the test; the prompt does not answer it.
            confirm += " You hold no capacity record to check it against."
        lines.append(
            f"- {o.description} ({lanes}): {o.transit_hours} hours from pickup; "
            f"using it raises the total to {_money(new_total)}.{confirm}"
        )
    options = "\n".join(lines)
    arrival_note = (
        f"\n\nWhen you quote an option, say when each lot would arrive at "
        f"{lg.destination}: its pickup time plus the quoted transit time."
        if lg.quotes_arrival
        else ""
    )
    return f"""\
You are the transport planning agent of {lg.organization}, a carrier.

{_COMMON}

What your organization can offer, to {lg.destination}:
{options}

In your organization, "delivery" is the transport service you perform: \
pickup at the supplier's origin plus the quoted transit time.

You plan from pickup time plus transit time. You do not know supplier terms, \
quantities or ready times unless the parties state them.{arrival_note}"""
