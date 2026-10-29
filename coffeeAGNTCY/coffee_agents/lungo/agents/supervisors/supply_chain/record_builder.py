# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Builds the commitment record from a strategy outcome (design D6).

The builder copies the Buyer's plan and the confirmations that were actually
received. It does not judge them: the status is the strategy's, and the
checker grades the record afterwards.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from agents.supervisors.supply_chain.outcome import Outcome, PlanLot
from agents.supply_chain.common import fixtures as fx
from agents.supply_chain.common.envelope import Envelope
from agents.supply_chain.common.record import CommitmentRecord, Confirmation, Lot


@dataclass
class RunFacts:
    run_id: str
    case: fx.CaseId
    configuration: str
    confirmations: list[Confirmation] = field(default_factory=list)
    disruption_injected: bool = False
    superseded_versions: list[int] = field(default_factory=list)
    log: list[Envelope] = field(default_factory=list)


def _words(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def normalize_option(name: str) -> str:
    """Map the option name the Buyer wrote to a fixture option id.

    The Buyer names an option the way Logistics did ("Standard road
    transport"). This only maps that wording to the fixture id; a name that
    matches nothing is kept as written, and the checker then reports it.
    """
    wanted = _words(name)
    for option in fx.load_scenario().logistics.options:
        if wanted in (_words(option.id), _words(option.description)):
            return option.id
    for option in fx.load_scenario().logistics.options:
        if _words(option.id) in wanted.split():
            return option.id
    return name


def _seqs(log: list[Envelope], party: str, kinds: tuple[str, ...]) -> list[int]:
    return [e.seq for e in log if e.sender == party and e.kind in kinds]


def _lot(lot: PlanLot, log: list[Envelope]) -> Lot:
    return Lot(
        supplier=lot.supplier,
        tonnes=lot.tonnes,
        grade=lot.grade,
        origin_ready_at=lot.origin_ready_at,
        transport_option=normalize_option(lot.transport_option),
        claimed_arrival_at=lot.claimed_arrival_at,
        evidence_seq=_seqs(log, lot.supplier, ("negotiation",)),
    )


def build_record(outcome: Outcome, facts: RunFacts) -> CommitmentRecord:
    buyer = fx.buyer_slice(facts.case).buyer
    plan = outcome.plan if outcome.status == "committed" else None

    record = CommitmentRecord(
        run_id=facts.run_id,
        case=facts.case,
        configuration=facts.configuration,  # type: ignore[arg-type]
        plan_version=outcome.plan_version,
        status=outcome.status,
        reason=outcome.reason,
        destination=buyer.destination,
        arrival_deadline=buyer.deadline,
        confirmations=list(facts.confirmations),
        disruption_injected=facts.disruption_injected,
        superseded_versions=list(facts.superseded_versions),
    )
    if plan is None:
        return record

    record.lots = [_lot(lot, facts.log) for lot in plan.lots]
    record.total_cost_usd = plan.total_cost_usd
    record.milestone = plan.milestone
    record.milestone_definition = plan.milestone_definition
    record.evidence = {
        "transport": _seqs(facts.log, "logistics", ("negotiation",)),
        "buyer_requirement": _seqs(facts.log, "buyer", ("negotiation",)),
        "confirmations": [c.seq for c in record.counted_confirmations().values()],
    }
    return record
