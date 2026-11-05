# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Decisions N25, lever C: the baseline plan does not clarify the milestone."""

from agents.supervisors.supply_chain.outcome import PlanLot, PlanProposal


def _lot() -> PlanLot:
    return PlanLot(
        supplier="supplier_a",
        tonnes=400,
        grade="Grade 1 washed Arabica, screen 17/18",
        transport_option="standard",
    )


def test_the_milestone_is_not_in_the_schema_the_model_sees():
    schema = PlanProposal.model_json_schema()
    assert "milestone" not in schema["properties"]
    assert "milestone_definition" not in schema["properties"]
    assert "milestone" not in str(schema)


def test_the_decision_instructions_do_not_ask_for_a_milestone():
    """Decisions N39: the plan has no field for it, so the prompt must not ask."""
    from agents.supervisors.supply_chain.strategies.baseline import (
        DECISION_INSTRUCTIONS,
    )

    assert "deadline measures" not in DECISION_INSTRUCTIONS
    assert "milestone" not in DECISION_INSTRUCTIONS


def test_the_decision_instructions_do_not_ask_for_a_milestone():
    """Decisions N39: the plan has no field for it, so the prompt must not ask."""
    from agents.supervisors.supply_chain.strategies.baseline import (
        DECISION_INSTRUCTIONS,
    )

    assert "deadline measures" not in DECISION_INSTRUCTIONS
    assert "milestone" not in DECISION_INSTRUCTIONS


def test_the_milestone_defaults_to_unspecified_and_is_not_rendered():
    plan = PlanProposal(lots=[_lot()], total_cost_usd=15000)
    assert plan.milestone == "unspecified"
    text = plan.render(1)
    assert "deadline refers to" not in text
    assert "unspecified" not in text


def test_code_can_still_set_the_milestone_and_it_is_rendered():
    plan = PlanProposal.model_validate(
        {
            "lots": [_lot().model_dump()],
            "milestone": "destination_receipt",
            "milestone_definition": "Received at Warehouse W.",
        }
    )
    text = plan.render(2)
    assert "The deadline refers to: destination_receipt" in text
    assert "Received at Warehouse W." in text


def test_the_confirm_request_does_not_show_claimed_arrival_times():
    """Decisions N25, lever D: the claim stays in the record, not in the request."""
    from datetime import datetime, timezone

    lot = _lot().model_copy(
        update={
            "origin_ready_at": datetime(2026, 11, 14, 9, tzinfo=timezone.utc),
            "claimed_arrival_at": datetime(2026, 11, 17, 9, tzinfo=timezone.utc),
        }
    )
    plan = PlanProposal(lots=[lot], total_cost_usd=15000)
    text = plan.render(1)
    assert "arrival" not in text
    assert "2026-11-17" not in text
    assert "ready at origin" not in text
    assert plan.lots[0].origin_ready_at is not None
    assert plan.lots[0].claimed_arrival_at is not None


def test_the_ready_time_is_kept_and_not_shown():
    """Decisions N46: the confirm request no longer prints the ready time."""
    from datetime import datetime, timedelta, timezone

    for ready in (
        datetime(2026, 11, 14, 9, tzinfo=timezone(timedelta(hours=2))),
        datetime(2026, 11, 14, 9),
    ):
        lot = _lot().model_copy(update={"origin_ready_at": ready})
        text = PlanProposal(lots=[lot]).render(1)
        assert "ready at origin" not in text
        assert lot.origin_ready_at == ready
