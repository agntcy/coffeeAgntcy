# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Reflection gates permission copy on AIMessage.additional_kwargs['supervisor_outcome'] (issue #495)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END

from agents.supervisors.auction.graph.graph import ExchangeGraph


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case_id,additional_kwargs,last_content,expect_replace,expected_substrings",
    [
        (
            "transport_tag_ignores_poison_reason",
            {"supervisor_outcome": "transport"},
            "I encountered an issue retrieving information from the Brazil farm. Please try again later.",
            False,
            [],
        ),
        (
            "no_tag_ignores_poison_reason",
            {},
            "I encountered an issue retrieving information from the Brazil farm. Please try again later.",
            False,
            [],
        ),
        (
            "permission_tag_replaces_with_issue_details",
            {"supervisor_outcome": "permission", "supervisor_farm": "brazil"},
            "I encountered an issue retrieving information from the Brazil farm. Please try again later.",
            True,
            [
                "Issue details:",
                "I encountered an issue retrieving information from the Brazil farm",
                "Brazil",
                "permission",
            ],
        ),
        (
            "permission_payment_kw_uses_mcp_template_without_payment_in_content",
            {"supervisor_outcome": "permission", "supervisor_operation": "payment"},
            "Tool reported authentication failure (code 403). Please try again later.",
            True,
            [
                "Issue details:",
                "Tool reported authentication failure",
                "Payment MCP",
                "'payment'",
            ],
        ),
        (
            "permission_farm_kw_prefers_kwargs_over_misleading_content",
            {"supervisor_outcome": "permission", "supervisor_farm": "colombia"},
            "Mention of Brazil in error text should not change farm template.",
            True,
            [
                "Issue details:",
                "Colombia",
                "Mention of Brazil in error text",
            ],
        ),
    ],
)
async def test_reflection_permission_replace_gated_by_supervisor_outcome(
    case_id,
    additional_kwargs,
    last_content,
    expect_replace,
    expected_substrings,
):
    graph = ExchangeGraph()
    graph.reflection_llm = MagicMock()
    decision = MagicMock()
    decision.should_continue = False
    decision.reason = "access permission identity denied for the farm"
    graph.reflection_llm.ainvoke = AsyncMock(return_value=decision)

    state = {
        "messages": [
            HumanMessage(content="What is the inventory of coffee in Brazil?"),
            AIMessage(
                content=last_content,
                additional_kwargs=additional_kwargs,
            ),
        ],
        "next_node": "",
    }

    out = await graph._reflection_node(state)

    if expect_replace:
        assert "messages" in out, case_id
        body = out["messages"][0].content
        for part in expected_substrings:
            assert part in body, f"{case_id}: expected {part!r} in {body!r}"
    else:
        assert "messages" not in out, case_id
        assert out.get("next_node") == END, case_id
