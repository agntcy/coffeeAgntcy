# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Role base prompts, shared by every configuration (design D4).

Each prompt is rendered from that party's own fixture slice only. The
organizational meaning of "delivery" differs by role, as the use case
specifies; no prompt states another party's data or the case's answer.
"""

from __future__ import annotations

from datetime import datetime

from agents.supply_chain.common.fixtures import (
    format_utc,
    BuyerSlice,
    LogisticsSlice,
    SupplierSlice,
)

# Bumped when a role prompt changes, so every saved run says which prompts it
# used (decisions N24/N25).
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
#      was graded as invented capacity; decisions N26).
#   (8: lever B, Logistics answers only what it is asked. Tried and reverted:
#      it made ambiguous and infeasible pass, see decisions N27.)
#   9: the explicit, infeasible and disruption openings give the deadline date
#      but not its time of day, which only the Buyer's brief holds (the
#      "hold time" lever, decisions N27).
PROMPT_VERSION = "9"

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
- The lot is ready at {p.origin} on {_ts(p.ready_at)}.

In your organization, a "delivery date" is the date goods are ready for \
pickup at your origin facility. You do not arrange or price transport."""


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
        if not o.available:
            lines.append(f"- {o.description} ({lanes}): no capacity is available.")
            continue
        new_total = base_total + sum(
            cost - base.lot_cost_usd[k] for k, cost in o.lot_cost_usd.items()
        )
        confirm = (
            " Its capacity must be explicitly confirmed by you."
            if o.requires_capacity_confirmation
            else ""
        )
        lines.append(
            f"- {o.description} ({lanes}): {o.transit_hours} hours from pickup; "
            f"using it raises the total to {_money(new_total)}.{confirm}"
        )
    options = "\n".join(lines)
    return f"""\
You are the transport planning agent of {lg.organization}, a carrier.

{_COMMON}

What your organization can offer, to {lg.destination}:
{options}

In your organization, "delivery" is the transport service you perform: \
pickup at the supplier's origin plus the quoted transit time.

You plan from pickup time plus transit time. You do not know supplier terms, \
quantities or ready times unless the parties state them."""
