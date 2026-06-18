# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for workflow capability derivation."""

from __future__ import annotations

from typing import NamedTuple

import pytest
from api.agentic_workflows.workflow_capabilities import derive_workflow_capabilities
from schema.types import Workflow


class CapCase(NamedTuple):
    case_id: str
    workflow: dict
    supports_sse: bool
    supports_streaming: bool
    chat_api_target: str | None


def _wf(payload: dict) -> Workflow:
    return Workflow.model_validate(payload)


_CAP_CASES: tuple[CapCase, ...] = (
    CapCase(
        case_id="publish_subscribe",
        workflow={
            "name": "Publish Subscribe",
            "pattern": "Supervisor",
            "use_case": "Purchasing",
            "scenario": "x",
            "starting_topology": {"nodes": [], "edges": []},
            "instances": {},
        },
        supports_sse=False,
        supports_streaming=False,
        chat_api_target="exchange",
    ),
    CapCase(
        case_id="publish_subscribe_streaming",
        workflow={
            "name": "Publish Subscribe Streaming",
            "pattern": "Supervisor",
            "use_case": "Purchasing",
            "scenario": "x",
            "starting_topology": {"nodes": [], "edges": []},
            "instances": {},
        },
        supports_sse=False,
        supports_streaming=True,
        chat_api_target="exchange",
    ),
    CapCase(
        case_id="group_messaging",
        workflow={
            "name": "Group Messaging",
            "pattern": "Supervisor",
            "use_case": "Order Fulfillment",
            "scenario": "x",
            "starting_topology": {
                "nodes": [
                    {
                        "id": "node://00000000-0000-4000-a000-000000000001",
                        "operation": "read",
                        "type": "group",
                        "label": "Logistics Group",
                        "size": {"width": 1.0, "height": 1.0},
                        "layer_index": 0,
                    },
                ],
                "edges": [],
            },
            "instances": {},
        },
        supports_sse=True,
        supports_streaming=False,
        chat_api_target="logistics",
    ),
    CapCase(
        case_id="a2a_http",
        workflow={
            "name": "A2A HTTP",
            "pattern": "Supervisor",
            "use_case": "Discovery",
            "scenario": "x",
            "starting_topology": {"nodes": [], "edges": []},
            "instances": {},
        },
        supports_sse=False,
        supports_streaming=True,
        chat_api_target="discovery",
    ),
    CapCase(
        case_id="placeholder",
        workflow={
            "name": "Orchestrator Agent",
            "pattern": "Supervisor",
            "use_case": "---",
            "scenario": "x",
            "starting_topology": {"nodes": [], "edges": []},
            "instances": {},
        },
        supports_sse=False,
        supports_streaming=False,
        chat_api_target=None,
    ),
)


@pytest.mark.parametrize("case", [pytest.param(c, id=c.case_id) for c in _CAP_CASES])
def test_derive_workflow_capabilities(case: CapCase) -> None:
    wf = _wf(case.workflow)
    sse, streaming, target = derive_workflow_capabilities(wf)
    assert sse == case.supports_sse
    assert streaming == case.supports_streaming
    assert target == case.chat_api_target
