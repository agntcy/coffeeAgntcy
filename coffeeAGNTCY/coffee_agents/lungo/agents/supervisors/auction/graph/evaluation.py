# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Second opinions from the evaluator agents, and the red-line rule.

Before the exchange buys coffee it asks the Quality Control and Sustainability
agents to grade every farm. Each viewpoint (price, quality, sustainability)
backs a different farm, so they often disagree. The rule that settles it is
plain code, not the LLM, so the demo is repeatable:

- Red line: a farm graded FAIL by any evaluator is blocked, however cheap.
- An evaluator that cannot be reached is reported openly; its view is
  missing, so it cannot block anything.

When an approved order then fails (farm offline, identity not verified),
the exchange re-routes to the next farm that passes every red line, but
never to one that costs more than the buyer offered without asking first.
"""

import asyncio
import logging
import os
import re
from dataclasses import dataclass, field

from agents.evaluators.quality_control.card import AGENT_CARD as QUALITY_CARD
from agents.evaluators.sustainability.card import AGENT_CARD as SUSTAINABILITY_CARD
from agents.scenario.profiles import load_farm_profiles
from agents.supervisors.auction.graph.tools import ask_evaluator, create_order

logger = logging.getLogger("lungo.supervisor.evaluation")

# viewpoint -> evaluator agent card
EVALUATORS = {
    "quality": QUALITY_CARD,
    "sustainability": SUSTAINABILITY_CARD,
}

# How long to wait on one farm or evaluator before treating it as offline.
# The SLIM transport can wait forever on an agent that has gone away, so the
# failover sets its own deadline instead of relying on the transport's.
AGENT_DEADLINE_SECONDS = float(os.getenv("FAILOVER_DEADLINE_SECONDS", "25"))

_ICONS = {"price": "💰", "quality": "☕", "sustainability": "🌱"}

# Matches the score lines both evaluators return, e.g.
# "brazil: score=70.0 grade=A (...)"
_SCORE_LINE = re.compile(r"^(\w+): score=([\d.]+) grade=(\w+)", re.MULTILINE)


@dataclass
class Evaluations:
    """Every viewpoint's grades for every farm, plus anything that went wrong."""

    prices: dict[str, float]
    # viewpoint -> farm -> (score, grade)
    grades: dict[str, dict[str, tuple[float, str]]] = field(default_factory=dict)
    # viewpoint -> error text, for evaluators that could not be reached
    errors: dict[str, str] = field(default_factory=dict)

    def red_line_failures(self, farm: str) -> list[str]:
        """Viewpoints that graded ``farm`` FAIL."""
        return [
            view
            for view, by_farm in self.grades.items()
            if by_farm.get(farm, (0, ""))[1] == "FAIL"
        ]

    def acceptable_farms(self) -> list[str]:
        """Farms no evaluator blocked, cheapest first."""
        ok = [f for f in self.prices if not self.red_line_failures(f)]
        return sorted(ok, key=self.prices.get)

    def favourite(self, view: str) -> str | None:
        """The farm a viewpoint would pick on its own."""
        if view == "price":
            return min(self.prices, key=self.prices.get)
        by_farm = self.grades.get(view)
        if not by_farm:
            return None
        return max(by_farm, key=lambda f: by_farm[f][0])


def parse_grades(report: str) -> dict[str, tuple[float, str]]:
    """Pull ``farm -> (score, grade)`` out of an evaluator's report."""
    return {
        farm.lower(): (float(score), grade.upper())
        for farm, score, grade in _SCORE_LINE.findall(report)
    }


async def gather_evaluations() -> Evaluations:
    """Ask every evaluator, in parallel, to grade all farms."""
    profiles = load_farm_profiles()
    evals = Evaluations(
        prices={farm: p["price_per_lb_usd"] for farm, p in profiles.items()}
    )
    prompt = "Assess all farms: " + ", ".join(profiles)

    results = await asyncio.gather(
        *(
            asyncio.wait_for(ask_evaluator(card, prompt), AGENT_DEADLINE_SECONDS)
            for card in EVALUATORS.values()
        ),
        return_exceptions=True,
    )
    for view, result in zip(EVALUATORS, results):
        if isinstance(result, BaseException):
            logger.warning("Evaluator %s unavailable: %s", view, result)
            evals.errors[view] = str(result)
            continue
        grades = parse_grades(result)
        if not grades:
            logger.warning("Evaluator %s returned no grades: %s", view, result)
            evals.errors[view] = "returned no grades"
            continue
        evals.grades[view] = grades
    return evals


def _grade_cell(evals: Evaluations, view: str, farm: str) -> str:
    if view in evals.errors:
        return "unavailable"
    score, grade = evals.grades[view].get(farm, (0.0, "?"))
    return f"{grade} ({score:g})"


def comparison_table(evals: Evaluations) -> str:
    """Markdown table of every farm against every viewpoint."""
    views = list(EVALUATORS)
    header = "| Farm | 💰 Price | " + " | ".join(
        f"{_ICONS[v]} {v.title()}" for v in views
    )
    lines = [header + " |", "|---" * (2 + len(views)) + "|"]
    for farm in sorted(evals.prices, key=evals.prices.get):
        cells = [_grade_cell(evals, v, farm) for v in views]
        lines.append(
            f"| {farm.title()} | ${evals.prices[farm]:.2f}/lb | "
            + " | ".join(cells)
            + " |"
        )
    return "\n".join(lines)


def viewpoints_summary(evals: Evaluations) -> str:
    """One line per viewpoint saying which farm it backs."""
    lines = []
    for view in ("price", *EVALUATORS):
        fav = evals.favourite(view)
        if fav:
            lines.append(f"- {_ICONS[view]} **{view.title()}** backs **{fav.title()}**")
        else:
            lines.append(f"- {_ICONS[view]} **{view.title()}**: no opinion (agent unavailable)")
    return "\n".join(lines)


def unavailable_note(evals: Evaluations) -> str:
    if not evals.errors:
        return ""
    names = ", ".join(v.title() for v in evals.errors)
    return (
        f"\n\n⚠️ Could not reach the {names} agent, so its red line was not checked."
    )


def blocked_order_message(evals: Evaluations, farm: str) -> str:
    """Explain why an order was refused and what would pass instead."""
    failed = evals.red_line_failures(farm)
    reasons = ", ".join(f"{_ICONS[v]} {v.title()}" for v in failed)
    alternatives = evals.acceptable_farms()
    if alternatives:
        options = ", ".join(
            f"{f.title()} (${evals.prices[f]:.2f}/lb)" for f in alternatives
        )
        next_step = f"Farms that pass every red line: {options}."
    else:
        next_step = "No farm passes every red line, so there is no deal to make."
    return (
        f"🛑 **Order blocked.** {farm.title()} failed the {reasons} red line.\n\n"
        f"{comparison_table(evals)}\n\n{next_step}{unavailable_note(evals)}"
    )


def approved_order_preamble(evals: Evaluations, farm: str) -> str:
    """Short note shown above a confirmed order."""
    cells = ", ".join(
        f"{_ICONS[v]} {v.title()} {_grade_cell(evals, v, farm)}" for v in EVALUATORS
    )
    return f"✅ **{farm.title()} passed every red line** ({cells}).{unavailable_note(evals)}"


def recommendation_message(evals: Evaluations) -> str:
    """Lay out the disagreement and what the red-line rule leaves on the table."""
    favourites = {evals.favourite(v) for v in ("price", *EVALUATORS)} - {None}
    if len(favourites) > 1:
        verdict = "⚖️ **The agents disagree.** No farm is everyone's first choice."
    else:
        verdict = "🤝 **The agents agree.**"

    blocked = [f for f in evals.prices if evals.red_line_failures(f)]
    blocked_text = (
        "\n".join(
            f"- 🛑 {f.title()} is blocked by "
            + ", ".join(v.title() for v in evals.red_line_failures(f))
            for f in blocked
        )
        or "- Nothing is blocked."
    )

    acceptable = evals.acceptable_farms()
    if not acceptable:
        outcome = "❌ **No farm passes every red line.** This disagreement is unresolved."
    elif len(acceptable) == 1:
        outcome = f"👉 **{acceptable[0].title()}** is the only farm every agent can accept."
    else:
        options = " or ".join(
            f"**{f.title()}** (${evals.prices[f]:.2f}/lb)" for f in acceptable
        )
        outcome = (
            f"🤔 Still open: {options} both pass every red line, but each agent "
            "prefers a different one. A human (or a negotiation) has to pick."
        )

    return (
        f"{verdict}\n\n{comparison_table(evals)}\n\n{viewpoints_summary(evals)}\n\n"
        f"**Red lines:**\n{blocked_text}\n\n{outcome}{unavailable_note(evals)}"
    )


# --- Placing an order, with failover -------------------------------------

_QUANTITY = re.compile(r"(\d[\d,]*)\s*(?:lb|lbs|pounds?)\b", re.IGNORECASE)
# "$3.10", "3.10 per lb", "3.10/lb"
_PRICE = re.compile(
    r"\$\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:/|per|a)\s*(?:lb|pound)\b",
    re.IGNORECASE,
)

_OUTCOME_TEXT = {
    "unreachable": "📴 offline, did not respond",
    "untrusted": "🔐 identity could not be verified, so it is not trusted",
    "error": "⚠️ the order failed",
}


@dataclass
class OrderAttempt:
    farm: str
    price: float
    # "placed", "unreachable", "untrusted", "error" or "needs_approval"
    outcome: str
    detail: str


def parse_order(text: str) -> tuple[int, float] | None:
    """Quantity (lb) and price per lb from an order request, if both are given."""
    qty = _QUANTITY.search(text)
    price = _PRICE.search(text)
    if not qty or not price:
        return None
    return int(qty.group(1).replace(",", "")), float(price.group(1) or price.group(2))


def _classify_failure(error: str) -> str:
    low = error.lower()
    if "identity" in low:
        return "untrusted"
    if any(t in low for t in ("communicate", "timed out", "no response", "unreachable")):
        return "unreachable"
    return "error"


async def place_order_with_failover(
    evals: Evaluations, farm: str, quantity: int, max_price: float
) -> list[OrderAttempt]:
    """Try ``farm``, then each other farm that passes every red line.

    Backups are tried cheapest first at their listed price, and skipped
    (pending the buyer's approval) when that is above what the buyer offered.
    """
    backups = [f for f in evals.acceptable_farms() if f != farm]
    attempts: list[OrderAttempt] = []
    for candidate in [farm, *backups]:
        price = max_price if candidate == farm else evals.prices[candidate]
        if price > max_price:
            attempts.append(
                OrderAttempt(
                    candidate,
                    price,
                    "needs_approval",
                    f"asks ${price:.2f}/lb, more than your ${max_price:.2f}/lb",
                )
            )
            continue
        try:
            result = await asyncio.wait_for(
                create_order.ainvoke(
                    {"farm": candidate, "quantity": quantity, "price": price}
                ),
                AGENT_DEADLINE_SECONDS,
            )
        except TimeoutError:
            logger.warning(
                "Order with %s got no reply in %ss", candidate, AGENT_DEADLINE_SECONDS
            )
            attempts.append(
                OrderAttempt(candidate, price, "unreachable", "no reply in time")
            )
            continue
        except Exception as e:
            outcome = _classify_failure(str(e))
            logger.warning("Order with %s failed (%s): %s", candidate, outcome, e)
            attempts.append(OrderAttempt(candidate, price, outcome, str(e)))
            continue
        attempts.append(OrderAttempt(candidate, price, "placed", str(result)))
        break
    return attempts


def order_outcome_message(
    evals: Evaluations, farm: str, quantity: int, attempts: list[OrderAttempt]
) -> str:
    """Explain every attempt and where the order ended up."""
    lines = [approved_order_preamble(evals, farm), "", "**What happened:**"]
    for i, a in enumerate(attempts, 1):
        if a.outcome == "placed":
            status = f"✅ order placed at ${a.price:.2f}/lb"
        elif a.outcome == "needs_approval":
            status = f"✋ {a.detail}, needs your OK"
        else:
            status = _OUTCOME_TEXT[a.outcome]
        lines.append(f"{i}. {a.farm.title()}: {status}")
    lines.append("")

    placed = next((a for a in attempts if a.outcome == "placed"), None)
    waiting = next((a for a in attempts if a.outcome == "needs_approval"), None)
    if placed and placed.farm == farm:
        lines.append(f"✅ **Order placed with {farm.title()}.**")
    elif placed:
        reason = _OUTCOME_TEXT[attempts[0].outcome].split(",")[0]
        lines.append(
            f"🔁 **Re-routed.** {farm.title()} failed ({reason}), so the order "
            f"went to {placed.farm.title()}, the next farm that passes every red line."
        )
    elif waiting:
        lines.append(
            f"⏸️ **Order on hold.** The only remaining option, {waiting.farm.title()}, "
            f"costs more than you offered. To approve, say: *Buy {quantity} lb from "
            f"{waiting.farm.title()} at {waiting.price:.2f} per lb*"
        )
    else:
        blocked = [f.title() for f in evals.prices if evals.red_line_failures(f)]
        lines.append(
            "❌ **Order not placed.** Every farm that passes the red lines failed."
            + (
                f" {', '.join(blocked)} could still sell, but the evaluators block it."
                if blocked
                else ""
            )
            + " This conflict is unresolved, so a human has to decide."
        )

    if placed:
        lines.append("")
        lines += [f"> {line}" for line in placed.detail.splitlines()]
    return "\n".join(lines)
