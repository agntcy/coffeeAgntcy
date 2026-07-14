# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for transport topology wire enrichment."""

from __future__ import annotations

from typing import NamedTuple

import pytest
from api.agentic_workflows.agent_ui_enrichment import clear_agent_ui_cache
from api.agentic_workflows.transport_ui_enrichment import (
    clear_transport_cache,
    enrich_topology_transport,
)
from tests.unit.agentic_workflows.catalog_test_helpers import init_transport_cache_for_tests

_TRANSPORT_NODE = {
    "id": "node://00000000-0000-4000-a000-000000000099",
    "operation": "read",
    "type": "transportNode",
    "label": "Transport",
    "size": {"width": 1.0, "height": 1.0},
    "layer_index": 2,
}


class TransportCase(NamedTuple):
    case_id: str
    chat_api_target: str | None
    expected_message_transport: str | None
    expected_label: str


@pytest.fixture(autouse=True)
def _reset_caches() -> None:
    clear_agent_ui_cache()
    clear_transport_cache()
    init_transport_cache_for_tests()
    yield
    clear_agent_ui_cache()
    clear_transport_cache()


_TRANSPORT_CASES: tuple[TransportCase, ...] = (
    TransportCase(
        case_id="group_messaging",
        chat_api_target="logistics",
        expected_message_transport="SLIM",
        expected_label="Transport: SLIM",
    ),
    TransportCase(
        case_id="publish_subscribe",
        chat_api_target="exchange",
        expected_message_transport="SLIM",
        expected_label="Transport: SLIM",
    ),
    TransportCase(
        case_id="a2a_http",
        chat_api_target="discovery",
        expected_message_transport=None,
        expected_label="Transport",
    ),
    TransportCase(
        case_id="placeholder",
        chat_api_target=None,
        expected_message_transport=None,
        expected_label="Transport",
    ),
)


@pytest.mark.parametrize("case", [pytest.param(c, id=c.case_id) for c in _TRANSPORT_CASES])
def test_enrich_topology_transport(case: TransportCase) -> None:
    topology = enrich_topology_transport(
        {"nodes": [_TRANSPORT_NODE], "edges": []},
        chat_api_target=case.chat_api_target,  # type: ignore[arg-type]
    )
    node = topology["nodes"][0]
    if case.expected_message_transport is None:
        assert "message_transport" not in node
        assert node["label"] == case.expected_label
    else:
        assert node["message_transport"] == case.expected_message_transport
        assert node["label"] == case.expected_label
