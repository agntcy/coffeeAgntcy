# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Builders for the models the Buyer's LLM fills in.

Those models have no defaulted fields (Azure strict structured output needs
every property in ``required``), so a test that only cares about a few fields
builds them here and gets the rest as "not stated".
"""

from __future__ import annotations

from typing import Any

from agents.supervisors.supply_chain.outcome import PlanLot, PlanProposal
from agents.supervisors.supply_chain.strategies.baseline import BuyerDecision


def plan_lot(**fields: Any) -> PlanLot:
    return PlanLot(**{"origin_ready_at": None, "claimed_arrival_at": None, **fields})


def plan_proposal(**fields: Any) -> PlanProposal:
    return PlanProposal(**{"total_cost_usd": None, **fields})


def buyer_decision(action: str, **fields: Any) -> BuyerDecision:
    return BuyerDecision(
        **{"action": action, "message": "", "plan": None, "reason": "", **fields}
    )
