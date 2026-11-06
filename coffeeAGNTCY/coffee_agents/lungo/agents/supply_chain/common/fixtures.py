# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Scenario fixtures and the per-party slices each agent may load.

Each agent process loads only its own slice (design D2). Only the checker
and the moderator's disruption injection use the full ``World`` view.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, model_validator

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
SCENARIO_PATH = FIXTURES_DIR / "scenario_v1.json"

CaseId = Literal["ambiguous", "explicit", "infeasible", "disruption"]
SupplierId = Literal["supplier_a", "supplier_b", "supplier_c"]
Party = Literal["buyer", "supplier_a", "supplier_b", "supplier_c", "logistics"]

CASES: tuple[CaseId, ...] = ("ambiguous", "explicit", "infeasible", "disruption")
SUPPLIERS: tuple[SupplierId, ...] = ("supplier_a", "supplier_b", "supplier_c")
PARTIES: tuple[Party, ...] = ("buyer", *SUPPLIERS, "logistics")


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class BuyerData(_Frozen):
    organization: str
    quantity_t: float
    grade: str
    destination: str
    deadline: datetime
    milestone: Literal["destination_receipt"]
    budget_usd: float


class SupplierData(_Frozen):
    name: str
    quantity_t: float
    grade: str
    origin: str
    # The true instant, in UTC. The checker uses only this.
    ready_at: datetime
    # The origin facility's clock, in hours from UTC. When it is not zero the
    # supplier's prompt gives the ready time on that clock and does not say
    # "UTC", the way a facility states its own time.
    utc_offset_hours: int = 0


class TransportOption(_Frozen):
    id: str
    description: str
    transit_hours: int
    lot_cost_usd: dict[SupplierId, float]
    # The truth, used by the checker.
    available: bool
    requires_capacity_confirmation: bool
    # False when the carrier holds no capacity record for this option, so its
    # prompt cannot say whether capacity exists. Then
    # ``available`` is a fact no party holds.
    capacity_known: bool = True


def name_words(text: str) -> str:
    """Lowercase words only, the form option names are compared in."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


class LogisticsData(_Frozen):
    organization: str
    destination: str
    options: tuple[TransportOption, ...]
    # The carrier states when each lot would arrive when it quotes an option,
    # so the Buyer can see a late lot.
    quotes_arrival: bool = False

    @model_validator(mode="after")
    def _names_are_unique(self) -> LogisticsData:
        # The agents only see descriptions and the record maps them back to an
        # id, so no id or description may read the same as another option's.
        owner: dict[str, str] = {}
        for option in self.options:
            if option.id in owner.values():
                raise ValueError(f"duplicate transport option id {option.id!r}")
            for name in {name_words(option.id), name_words(option.description)}:
                if owner.setdefault(name, option.id) != option.id:
                    raise ValueError(
                        f"transport options {owner[name]!r} and {option.id!r} "
                        f"share the name {name!r}"
                    )
        return self


class Disruption(_Frozen):
    supplier: SupplierId
    ready_at: datetime
    supplier_notice: str
    group_notice: str


class SupplierOverride(_Frozen):
    """What differs for one supplier in one case; ``None`` keeps the shared value."""

    ready_at: datetime | None = None
    utc_offset_hours: int | None = None


class Case(_Frozen):
    description: str
    buyer_wording: str
    logistics_overrides: dict[str, dict[str, bool]]
    disruption: Disruption | None
    # The Buyer's deadline for this case when it differs from the shared one
    # (``disruption`` is on time before the delay).
    deadline: datetime | None = None
    # A supplier whose ready time or clock differs in this case.
    supplier_overrides: dict[SupplierId, SupplierOverride] = {}
    # Logistics states each lot's arrival time when it quotes.
    logistics_quotes_arrival: bool = False


class Scenario(_Frozen):
    version: int
    simulated: Literal[True]
    source: str
    notes: tuple[str, ...]
    buyer: BuyerData
    suppliers: dict[SupplierId, SupplierData]
    logistics: LogisticsData
    cases: dict[CaseId, Case]


class BuyerSlice(_Frozen):
    case: CaseId
    buyer: BuyerData
    opening_wording: str
    # Facilities whose clock is not UTC: (origin, hours from UTC). Only the
    # Buyer holds this; a supplier states its own wall time.
    facility_clocks: tuple[tuple[str, int], ...] = ()


class SupplierSlice(_Frozen):
    case: CaseId
    supplier_id: SupplierId
    supplier: SupplierData


class LogisticsSlice(_Frozen):
    case: CaseId
    logistics: LogisticsData


class World(_Frozen):
    """The full effective scenario for one case. Checker use only."""

    case: CaseId
    disrupted: bool
    buyer: BuyerData
    suppliers: dict[SupplierId, SupplierData]
    options: tuple[TransportOption, ...]

    def option(self, option_id: str) -> TransportOption | None:
        return next((o for o in self.options if o.id == option_id), None)

    def arrival(self, supplier_id: SupplierId, option: TransportOption) -> datetime:
        ready = self.suppliers[supplier_id].ready_at
        return ready + timedelta(hours=option.transit_hours)


@lru_cache(maxsize=4)
def format_utc(value: datetime) -> str:
    """A time as the agents read it in their prompts, e.g. "November 18, 17:00 UTC"."""
    return f"{value:%B} {value.day}, {value:%H:%M} UTC"


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    keys = [key for key, _ in pairs]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise ValueError(f"duplicate keys in scenario file: {duplicates}")
    return dict(pairs)


def load_scenario(path: Path = SCENARIO_PATH) -> Scenario:
    data = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys
    )
    return Scenario.model_validate(data)


def _buyer_for(scenario: Scenario, case_id: CaseId) -> BuyerData:
    deadline = scenario.cases[case_id].deadline
    if deadline is None:
        return scenario.buyer
    return scenario.buyer.model_copy(update={"deadline": deadline})


def _logistics_for(scenario: Scenario, case_id: CaseId) -> LogisticsData:
    overrides = scenario.cases[case_id].logistics_overrides
    options = tuple(
        o.model_copy(update=overrides.get(o.id, {})) for o in scenario.logistics.options
    )
    return scenario.logistics.model_copy(
        update={
            "options": options,
            "quotes_arrival": scenario.cases[case_id].logistics_quotes_arrival,
        }
    )


def _supplier_for(
    scenario: Scenario, supplier_id: SupplierId, case_id: CaseId, disrupted: bool
) -> SupplierData:
    data = scenario.suppliers[supplier_id]
    override = scenario.cases[case_id].supplier_overrides.get(supplier_id)
    if override is not None:
        data = data.model_copy(update=override.model_dump(exclude_none=True))
    disruption = scenario.cases[case_id].disruption
    if disrupted and disruption is not None and disruption.supplier == supplier_id:
        return data.model_copy(update={"ready_at": disruption.ready_at})
    return data


def buyer_slice(case_id: CaseId, scenario: Scenario | None = None) -> BuyerSlice:
    scenario = scenario or load_scenario()
    clocks = tuple(
        (data.origin, data.utc_offset_hours)
        for sid in scenario.suppliers
        for data in [_supplier_for(scenario, sid, case_id, False)]
        if data.utc_offset_hours != 0
    )
    return BuyerSlice(
        case=case_id,
        buyer=_buyer_for(scenario, case_id),
        opening_wording=scenario.cases[case_id].buyer_wording,
        facility_clocks=clocks,
    )


def supplier_slice(
    supplier_id: SupplierId,
    case_id: CaseId,
    disrupted: bool = False,
    scenario: Scenario | None = None,
) -> SupplierSlice:
    scenario = scenario or load_scenario()
    return SupplierSlice(
        case=case_id,
        supplier_id=supplier_id,
        supplier=_supplier_for(scenario, supplier_id, case_id, disrupted),
    )


def logistics_slice(
    case_id: CaseId, scenario: Scenario | None = None
) -> LogisticsSlice:
    scenario = scenario or load_scenario()
    return LogisticsSlice(case=case_id, logistics=_logistics_for(scenario, case_id))


def world(
    case_id: CaseId, disrupted: bool = False, scenario: Scenario | None = None
) -> World:
    scenario = scenario or load_scenario()
    return World(
        case=case_id,
        disrupted=disrupted,
        buyer=_buyer_for(scenario, case_id),
        suppliers={
            s: _supplier_for(scenario, s, case_id, disrupted)
            for s in scenario.suppliers
        },
        options=_logistics_for(scenario, case_id).options,
    )


def disruption_for(
    case_id: CaseId, scenario: Scenario | None = None
) -> Disruption | None:
    scenario = scenario or load_scenario()
    return scenario.cases[case_id].disruption
