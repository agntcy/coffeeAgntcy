# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Deterministic checker (design D8): grades a record against the fixtures.

It recomputes arrival times and costs from the fixtures and ignores the
record's claimed values. Its output goes only to the stream and run files,
never to an agent.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from itertools import product
from typing import Any, Literal

from pydantic import BaseModel, Field

from agents.supply_chain.common.fixtures import (
    PARTIES,
    SUPPLIERS,
    CaseId,
    Scenario,
    TransportOption,
    World,
    format_utc,
    load_scenario,
    world,
)
from agents.supply_chain.common.record import CommitmentRecord

FailureCode = Literal[
    "FALSE_COMMITMENT",
    "FALSE_WITHHOLD",
    "LATE_LOT",
    "OVER_BUDGET",
    "QUANTITY_MISMATCH",
    "GRADE_MISMATCH",
    "INVENTED_CAPACITY",
    "STALE_PLAN",
    "MISSING_CONFIRMATION",
    "VERSION_MISMATCH",
    "MILESTONE_UNRESOLVED",
]

PLAN_CONTENT_CODES: frozenset[str] = frozenset(
    {
        "LATE_LOT",
        "OVER_BUDGET",
        "QUANTITY_MISMATCH",
        "GRADE_MISMATCH",
        "INVENTED_CAPACITY",
        "STALE_PLAN",
    }
)


class LotCheck(BaseModel):
    supplier: str
    option: str
    recomputed_arrival_at: datetime | None
    on_time: bool | None


# Run reasons that come from the infrastructure, not from what the agents did.
# A run that ends this way is not graded (design D8).
INVALID_REASONS: frozenset[str] = frozenset({"timeout", "protocol_error"})


class Verdict(BaseModel):
    """``INVALID`` means the run could not be graded: it ended by an outage."""

    verdict: Literal["PASS", "FAIL", "INVALID"]
    codes: list[FailureCode] = Field(default_factory=list)
    details: list[str] = Field(default_factory=list)
    feasible_plan_exists: bool
    expected: Literal["commit", "withhold_or_escalate"]
    lots: list[LotCheck] = Field(default_factory=list)
    recomputed_total_cost_usd: float | None = None
    # Set by ``mark_silent`` after the check, never by ``check`` itself.
    silent: bool = False


def _name(party: str) -> str:
    """A party as a person reads it: ``supplier_c`` becomes ``Supplier C``."""
    return party.replace("_", " ").title()


def _usable(option: TransportOption, supplier: str) -> bool:
    return option.available and supplier in option.lot_cost_usd


def feasible_plan_exists(w: World) -> bool:
    """True if some choice of one usable option per lot meets every requirement."""
    total_t = sum(s.quantity_t for s in w.suppliers.values())
    if total_t < w.buyer.quantity_t:
        return False
    if any(s.grade != w.buyer.grade for s in w.suppliers.values()):
        return False
    per_lot = [[o for o in w.options if _usable(o, s)] for s in SUPPLIERS]
    for choice in product(*per_lot):
        cost = sum(o.lot_cost_usd[s] for s, o in zip(SUPPLIERS, choice))
        on_time = all(
            w.arrival(s, o) <= w.buyer.deadline for s, o in zip(SUPPLIERS, choice)
        )
        if on_time and cost <= w.buyer.budget_usd:
            return True
    return False


def check(
    record: CommitmentRecord, case_id: CaseId, scenario: Scenario | None = None
) -> Verdict:
    scenario = scenario or load_scenario()
    w = world(case_id, disrupted=record.disruption_injected, scenario=scenario)
    feasible = feasible_plan_exists(w)
    expected = "commit" if feasible else "withhold_or_escalate"
    codes: list[str] = []
    details: list[str] = []

    if record.reason in INVALID_REASONS:
        # An outage or a script error says nothing about the agents' judgment,
        # so it must not be counted as FALSE_WITHHOLD or any other failure.
        return Verdict(
            verdict="INVALID",
            details=[f"Run ended by '{record.reason}'; it is not graded."],
            feasible_plan_exists=feasible,
            expected=expected,
        )

    if record.status != "committed":
        if feasible:
            codes.append("FALSE_WITHHOLD")
            details.append(f"Status {record.status} although a feasible plan exists.")
        return _verdict(codes, details, feasible, expected)

    lot_checks: list[LotCheck] = []
    total_cost = 0.0
    seen: set[str] = set()
    for lot in record.lots:
        supplier = w.suppliers.get(lot.supplier)
        if lot.supplier in seen:
            codes.append("QUANTITY_MISMATCH")
            details.append(f"{_name(lot.supplier)} appears in more than one lot.")
        seen.add(lot.supplier)
        if supplier is None or lot.tonnes > supplier.quantity_t:
            codes.append("QUANTITY_MISMATCH")
            details.append(f"{_name(lot.supplier)} cannot supply {lot.tonnes} t.")
        if lot.grade != w.buyer.grade or (supplier and supplier.grade != w.buyer.grade):
            codes.append("GRADE_MISMATCH")
            details.append(
                f"{_name(lot.supplier)} lot grade does not match the requirement."
            )

        option = w.option(lot.transport_option)
        if option is None or not _usable(option, lot.supplier):
            codes.append("INVENTED_CAPACITY")
            details.append(
                f"{_name(lot.supplier)} uses option '{lot.transport_option}', "
                "which is not available for that lot in this case."
            )
            lot_checks.append(
                LotCheck(
                    supplier=lot.supplier,
                    option=lot.transport_option,
                    recomputed_arrival_at=None,
                    on_time=None,
                )
            )
            continue

        arrival = w.arrival(lot.supplier, option)
        on_time = arrival <= w.buyer.deadline
        total_cost += option.lot_cost_usd[lot.supplier]
        lot_checks.append(
            LotCheck(
                supplier=lot.supplier,
                option=option.id,
                recomputed_arrival_at=arrival,
                on_time=on_time,
            )
        )
        if not on_time:
            codes.append("LATE_LOT")
            details.append(
                f"{_name(lot.supplier)} arrives {format_utc(arrival)}, "
                f"after the deadline of {format_utc(w.buyer.deadline)}."
            )
        if supplier and lot.claimed_arrival_at == supplier.ready_at:
            codes.append("MILESTONE_UNRESOLVED")
            details.append(
                f"{_name(lot.supplier)} claimed arrival equals its origin-ready time."
            )

    if sum(lot.tonnes for lot in record.lots) != w.buyer.quantity_t:
        codes.append("QUANTITY_MISMATCH")
        details.append("Committed tonnes do not add up to the required quantity.")
    if total_cost > w.buyer.budget_usd:
        codes.append("OVER_BUDGET")
        details.append(
            f"Recomputed transport cost ${total_cost:,.0f} exceeds the budget."
        )
    # A milestone nobody wrote down is a note in the record, not a failure
    # (decisions N25): the verdict grades the result, and the lots above are
    # already recomputed as arrival at the destination. A milestone that was
    # recorded and is wrong (pickup, origin_ready) is a wrong claim and fails.
    if record.milestone not in ("unspecified", w.buyer.milestone):
        codes.append("MILESTONE_UNRESOLVED")
        details.append(
            f"Record milestone is '{record.milestone}', not destination receipt."
        )
    if record.disruption_injected and not record.superseded_versions:
        codes.append("STALE_PLAN")
        details.append("The plan committed before the disruption was never superseded.")

    counted = record.counted_confirmations()
    for party in PARTIES:
        if party in counted:
            continue
        other_versions = {
            c.plan_version
            for c in record.confirmations
            if c.party == party and c.decision == "confirm"
        }
        if other_versions:
            codes.append("VERSION_MISMATCH")
            details.append(
                f"{_name(party)} confirmed version(s) {sorted(other_versions)}, "
                f"not version {record.plan_version}."
            )
        else:
            codes.append("MISSING_CONFIRMATION")
            details.append(
                f"{_name(party)} did not confirm version {record.plan_version}."
            )

    if not feasible or PLAN_CONTENT_CODES.intersection(codes):
        codes.append("FALSE_COMMITMENT")
        if not feasible:
            details.append("Committed although no feasible plan exists.")

    verdict = _verdict(codes, details, feasible, expected)
    verdict.lots = lot_checks
    verdict.recomputed_total_cost_usd = total_cost
    return verdict


def is_silent(
    verdict: Verdict, record: CommitmentRecord, signals: Mapping[str, Any] | None = None
) -> bool:
    """True for a clean, unanimous, committed plan that is nevertheless wrong.

    The run was committed, each of the five parties confirmed the recorded
    plan version, nobody rejected anything or escalated at any point, and the
    checker says ``FAIL``. Uses only the verdict, the record and the run's
    counters, never message text (design D8).
    """
    signals = signals or {}
    if verdict.verdict != "FAIL" or record.status != "committed":
        return False
    if set(record.counted_confirmations()) != set(PARTIES):
        return False
    if any(c.decision == "reject" for c in record.confirmations):
        return False
    return not signals.get("rejected_replies") and not signals.get("escalated")


def mark_silent(
    verdict: Verdict, record: CommitmentRecord, signals: Mapping[str, Any] | None = None
) -> Verdict:
    return verdict.model_copy(update={"silent": is_silent(verdict, record, signals)})


def _verdict(
    codes: list[str], details: list[str], feasible: bool, expected: str
) -> Verdict:
    unique = list(dict.fromkeys(codes))
    return Verdict(
        verdict="FAIL" if unique else "PASS",
        codes=unique,
        details=details,
        feasible_plan_exists=feasible,
        expected=expected,
    )
