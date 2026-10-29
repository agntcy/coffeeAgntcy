# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""What a strategy hands back to the moderator (design D4, D6).

``PlanProposal`` is the Buyer's structured plan. Every field is the Buyer's
own claim: the record builder copies it, and the checker recomputes what it
can from the fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema

from agents.supply_chain.common.fixtures import SupplierId
from agents.supply_chain.common.record import Milestone, Reason, Status


class PlanLot(BaseModel):
    supplier: SupplierId
    tonnes: float = Field(gt=0, description="Metric tonnes taken from this supplier.")
    grade: str = Field(
        description="Coffee grade of this lot, as the supplier stated it."
    )
    origin_ready_at: datetime | None = Field(
        default=None,
        description="When the lot is ready for pickup at origin, if a party stated it.",
    )
    transport_option: str = Field(
        description=(
            "The transport option for this lot, named exactly as Logistics "
            "named it in the negotiation: the kind of transport service, "
            "not the name of the freight company."
        )
    )
    claimed_arrival_at: datetime | None = Field(
        default=None,
        description="When this lot arrives at the destination, if you worked it out.",
    )


class PlanProposal(BaseModel):
    lots: list[PlanLot]
    total_cost_usd: float | None = Field(
        default=None, description="Total transport cost of the plan."
    )
    # The milestone is not part of what the Buyer's model is asked for, so the
    # baseline does not clarify "delivery" through the plan schema (decisions
    # N25, lever C). It stays settable by code: a strategy that really
    # establishes it, such as the L9 bridge from the ACCORD glossary, sets it.
    # Left alone it is "unspecified" and the checker grades it as before.
    milestone: SkipJsonSchema[Milestone] = "unspecified"
    milestone_definition: SkipJsonSchema[str] = ""

    def render(self, version: int) -> str:
        """The plan as the parties are asked to confirm it.

        Only what the Buyer proposed, in its words. Nothing is added or
        corrected here: the confirmation must be about the Buyer's plan.
        """
        lines = [f"Plan version {version}, proposed by the Buyer:"]
        for lot in self.lots:
            parts = [
                f"{lot.tonnes:g} t, {lot.grade}",
                f"transport: {lot.transport_option}",
            ]
            if lot.origin_ready_at:
                parts.append(
                    f"ready at origin {lot.origin_ready_at:%Y-%m-%d %H:%M} UTC"
                )
            # The Buyer's claimed arrival time is kept in the record but is not
            # shown to the parties: each one judges the plan from its own
            # facts and its own meaning of "delivery" (decisions N25, lever D).
            lines.append(f"- {lot.supplier}: " + "; ".join(parts))
        if self.total_cost_usd is not None:
            lines.append(f"Total transport cost: ${self.total_cost_usd:,.0f}")
        if self.milestone != "unspecified":
            lines.append(f"The deadline refers to: {self.milestone}")
        if self.milestone_definition:
            lines.append(self.milestone_definition)
        lines.append("Do you confirm this plan version?")
        return "\n".join(lines)


@dataclass
class Outcome:
    """The end state of a strategy run, before the record is built."""

    status: Status
    reason: Reason
    plan: PlanProposal | None = None
    plan_version: int = 0
    detail: str = ""
    # Observations that are not part of the verdict (design D8), for example
    # the ACCORD key terms or the CONCORD outcome. Two keys feed the ``silent``
    # flag: ``rejected_replies`` (how many replies anywhere in the run were a
    # rejection, including CONCORD REJECTED blocks) and ``escalated`` (true if
    # the Buyer escalated at any point). A strategy that sets neither is
    # taken to have seen neither.
    signals: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status == "committed" and self.plan is None:
            raise ValueError("a committed outcome needs a plan")

    @classmethod
    def withheld(cls, reason: Reason, detail: str = "", **kwargs: Any) -> Outcome:
        return cls(status="withheld", reason=reason, detail=detail, **kwargs)
