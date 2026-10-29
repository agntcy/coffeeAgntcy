# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Scenario fixtures and the per-party slices each agent may load.

Each agent process loads only its own slice (design D2). Only the checker
and the moderator's disruption injection use the full ``World`` view.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

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
    ready_at: datetime


class TransportOption(_Frozen):
    id: str
    description: str
    transit_hours: int
    lot_cost_usd: dict[SupplierId, float]
    available: bool
    requires_capacity_confirmation: bool


class LogisticsData(_Frozen):
    organization: str
    destination: str
    options: tuple[TransportOption, ...]


class Disruption(_Frozen):
    supplier: SupplierId
    ready_at: datetime
    supplier_notice: str
    group_notice: str


class Case(_Frozen):
    description: str
    buyer_wording: str
    logistics_overrides: dict[str, dict[str, bool]]
    disruption: Disruption | None


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


def load_scenario(path: Path = SCENARIO_PATH) -> Scenario:
    return Scenario.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _logistics_for(scenario: Scenario, case_id: CaseId) -> LogisticsData:
    overrides = scenario.cases[case_id].logistics_overrides
    options = tuple(
        o.model_copy(update=overrides.get(o.id, {})) for o in scenario.logistics.options
    )
    return scenario.logistics.model_copy(update={"options": options})


def _supplier_for(
    scenario: Scenario, supplier_id: SupplierId, case_id: CaseId, disrupted: bool
) -> SupplierData:
    data = scenario.suppliers[supplier_id]
    disruption = scenario.cases[case_id].disruption
    if disrupted and disruption is not None and disruption.supplier == supplier_id:
        return data.model_copy(update={"ready_at": disruption.ready_at})
    return data


def buyer_slice(case_id: CaseId, scenario: Scenario | None = None) -> BuyerSlice:
    scenario = scenario or load_scenario()
    return BuyerSlice(
        case=case_id,
        buyer=scenario.buyer,
        opening_wording=scenario.cases[case_id].buyer_wording,
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
        buyer=scenario.buyer,
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
