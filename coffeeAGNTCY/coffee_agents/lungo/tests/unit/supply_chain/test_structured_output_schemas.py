# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""The models the LLM fills in must be valid for strict structured output.

Azure OpenAI validates a strict ``response_format`` schema up front: every
property of every object must be listed in ``required``, and some keywords
are not supported. A model with a defaulted field is accepted by the LiteLLM
proxy path but rejected with a 400 on the Azure path, which ends the run as
``protocol_error``.
"""

import pytest

from agents.supervisors.supply_chain.outcome import PlanLot, PlanProposal
from agents.supervisors.supply_chain.selection import _Extracted
from agents.supervisors.supply_chain.strategies.baseline import BuyerDecision
from agents.supply_chain.common.member import ConfirmDecision
from tests.helpers.supply_chain_schemas import strict_violations


@pytest.mark.parametrize(
    "model",
    [BuyerDecision, ConfirmDecision, PlanLot, PlanProposal, _Extracted],
    ids=lambda m: m.__name__,
)
def test_the_schema_is_valid_for_strict_structured_output(model):
    assert strict_violations(model.model_json_schema()) == []


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
