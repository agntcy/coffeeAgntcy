# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""The models the LLM fills in must be valid for strict structured output.

Azure OpenAI validates a strict ``response_format`` schema up front: every
property of every object must be listed in ``required``, and some keywords
are not supported. A model with a defaulted field is accepted by the LiteLLM
proxy path but rejected with a 400 on the Azure path, which ends the run as
``protocol_error``.
"""

from typing import Any

import pytest

from agents.supervisors.supply_chain.outcome import PlanLot, PlanProposal
from agents.supervisors.supply_chain.selection import _Extracted
from agents.supervisors.supply_chain.strategies.baseline import BuyerDecision
from agents.supply_chain.common.member import ConfirmDecision

# Keywords that Azure strict mode does not accept, as far as we have seen.
UNSUPPORTED = {"exclusiveMinimum", "exclusiveMaximum", "minimum", "maximum"}


def _walk(node: Any, path: str = "#"):
    if isinstance(node, dict):
        yield path, node
        for key, value in node.items():
            yield from _walk(value, f"{path}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, f"{path}/{index}")


def _violations(model) -> list[str]:
    found = []
    for path, node in _walk(model.model_json_schema()):
        properties = node.get("properties")
        if isinstance(properties, dict) and "type" in node:
            missing = set(properties) - set(node.get("required", []))
            if missing:
                found.append(f"{path}: not required: {sorted(missing)}")
        for keyword in UNSUPPORTED & node.keys():
            if path.rsplit("/", 1)[-1] != "properties":
                found.append(f"{path}: unsupported keyword {keyword}")
    return found


@pytest.mark.parametrize(
    "model",
    [BuyerDecision, ConfirmDecision, PlanLot, PlanProposal, _Extracted],
    ids=lambda m: m.__name__,
)
def test_the_schema_is_valid_for_strict_structured_output(model):
    assert _violations(model) == []


def test_a_plan_lot_with_no_tonnes_is_refused_by_the_decision_check():
    """``gt=0`` left the schema, so the Buyer decision check enforces it."""
    from agents.supervisors.supply_chain.strategies.baseline import (
        validate_decision,
    )
    from agents.supervisors.supply_chain.moderator import StepFailed

    lot = PlanLot(
        supplier="supplier_a",
        tonnes=0,
        grade="G",
        origin_ready_at=None,
        transport_option="standard",
        claimed_arrival_at=None,
    )
    decision = BuyerDecision(
        action="propose_plan",
        message="",
        plan=PlanProposal(lots=[lot], total_cost_usd=None),
        reason="",
    )
    with pytest.raises(StepFailed):
        validate_decision(decision)
