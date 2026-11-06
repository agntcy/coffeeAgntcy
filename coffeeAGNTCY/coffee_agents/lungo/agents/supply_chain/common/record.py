# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Structured commitment record produced by every run (design D6)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from agents.supply_chain.common.fixtures import FIXTURES_DIR, CaseId, Party, SupplierId

RECORD_SCHEMA_PATH = FIXTURES_DIR / "commitment_record_v1.schema.json"

Status = Literal["committed", "withheld", "escalated"]
Reason = Literal[
    "buyer_decision",
    "party_rejected",
    "round_limit",
    "timeout",
    "protocol_error",
    "no_feasible_revision",
]
Milestone = Literal["destination_receipt", "pickup", "origin_ready", "unspecified"]
Configuration = Literal["baseline", "l9_hybrid", "l9_full"]


class Lot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier: SupplierId
    tonnes: float = Field(gt=0)
    grade: str
    origin_ready_at: datetime | None = None
    transport_option: str
    claimed_arrival_at: datetime | None = None
    evidence_seq: list[int] = Field(default_factory=list)


class Confirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    party: Party
    plan_version: int = Field(ge=1)
    decision: Literal["confirm", "reject"]
    seq: int = Field(ge=0)
    reason: str = ""


class CommitmentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulated: Literal[True] = True
    run_id: str
    case: CaseId
    configuration: Configuration
    plan_version: int = Field(default=0, ge=0)
    status: Status
    reason: Reason
    lots: list[Lot] = Field(default_factory=list)
    destination: str | None = None
    arrival_deadline: datetime | None = None
    total_cost_usd: float | None = None
    milestone: Milestone = "unspecified"
    milestone_definition: str = ""
    confirmations: list[Confirmation] = Field(
        default_factory=list,
        description="Every confirmation received in the run, for any plan version.",
    )
    evidence: dict[str, list[int]] = Field(
        default_factory=dict,
        description="Record field name to the message seq numbers supporting it.",
    )
    disruption_injected: bool = False
    superseded_versions: list[int] = Field(default_factory=list)

    def counted_confirmations(self) -> dict[Party, Confirmation]:
        """Confirmations that count: ``confirm``, sent for this plan version."""
        counted: dict[Party, Confirmation] = {}
        for c in self.confirmations:
            if c.decision == "confirm" and c.plan_version == self.plan_version:
                counted[c.party] = c
        return counted


def record_json_schema() -> dict:
    return CommitmentRecord.model_json_schema()


def write_record_schema(path: Path = RECORD_SCHEMA_PATH) -> None:
    path.write_text(json.dumps(record_json_schema(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_record_schema()
