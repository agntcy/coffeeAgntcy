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


_words = fx.name_words


# Words a correct option name may carry beyond the fixture vocabulary.
# The second line comes from Buyer wordings in real baseline runs.
_PLAIN_WORDS = frozenset(
    "the transport freight service option shipping by via for to lot lots "
    "hours hour h "
    "delivery transit only optional shipment from origin facility logistics s".split()
)
# Never "known", even if a fixture description ever uses one.
_NEGATORS = frozenset(
    "not no non nor neither never cannot cant t without except avoid instead "
    "rather than unlike versus vs unavailable infeasible impossible unable".split()
)
_AMOUNT = re.compile(r"\d+[a-z]*")  # "60", "48h"


def normalize_option(name: str) -> str:
    """Map the option name the Buyer wrote to a fixture option id.

    Exact id or description match wins. Otherwise the text is mapped only if
    every word is known (fixture vocabulary, a short plain-word list, or an
    amount such as 48h) and exactly one option id appears as a whole word.
    Anything else is kept as written, so the checker reports it instead of
    the mapper guessing.
    """
    wanted = _words(name)
    scenario = fx.load_scenario()
    options = scenario.logistics.options
    for option in options:
        if wanted in (_words(option.id), _words(option.description)):
            return option.id
    known = set(_PLAIN_WORDS)
    for text in (
        scenario.logistics.organization,
        scenario.logistics.destination,
        *scenario.suppliers,
        *(o.id for o in options),
        *(o.description for o in options),
    ):
        known.update(_words(text).split())
    known -= _NEGATORS
    tokens = wanted.split()
    if any(t not in known and not _AMOUNT.fullmatch(t) for t in tokens):
        return name
    padded = f" {wanted} "
    hits = [o.id for o in options if f" {_words(o.id)} " in padded]
    return hits[0] if len(hits) == 1 else name


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
