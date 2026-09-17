# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for label-based remapping of starting_topology edge endpoints after node id rotation."""

from __future__ import annotations

import pytest

from api.agentic_workflows.workflows import (
    _remap_starting_topology_edge_endpoints,
    _require_old_id_to_unique_label,
)
from schema.types import Edge, NodeId, Operation, PartialEdge, PartialBaseNode, BaseNode


def _edge(
    eid: str,
    source: str,
    target: str,
) -> Edge:
    return Edge.model_validate(
        {
            "id": eid,
            "operation": Operation.READ.value,
            "type": "custom",
            "source": source,
            "target": target,
            "bidirectional": False,
            "weight": 1.0,
        }
    )


def _base_node(nid: str, label: str) -> BaseNode:
    return BaseNode.model_validate(
        {
            "id": nid,
            "operation": Operation.READ.value,
            "type": "customNode",
            "label": label,
            "size": {"width": 1.0, "height": 1.0},
            "layer_index": 0,
        }
    )


def test_remap_full_edge_endpoints_using_labels() -> None:
    old_a = "node://aaaaaaaa-0000-4000-a000-000000000001"
    old_b = "node://bbbbbbbb-0000-4000-a000-000000000002"
    new_a = "node://11111111-1111-4111-a111-111111111111"
    new_b = "node://22222222-2222-4222-a222-222222222222"
    edge = _edge("edge://eeeeeeee-0000-4000-a000-e00000000001", old_a, old_b)
    old_id_to_label = {old_a: "Alpha", old_b: "Beta"}
    label_to_new_id = {"Alpha": new_a, "Beta": new_b}

    _remap_starting_topology_edge_endpoints(
        [edge],
        old_id_to_label,
        label_to_new_id,
        workflow_name="TestWf",
        idx_wf=0,
    )

    assert edge.source == NodeId(new_a)
    assert edge.target == NodeId(new_b)


def test_remap_partial_edge_optional_endpoints() -> None:
    pe = PartialEdge.model_validate(
        {
            "id": "edge://eeeeeeee-0000-4000-a000-e00000000002",
            "operation": Operation.READ.value,
            "source": "node://aaaaaaaa-0000-4000-a000-000000000003",
            "target": None,
            "bidirectional": False,
            "weight": 1.0,
        }
    )
    old = "node://aaaaaaaa-0000-4000-a000-000000000003"
    new = "node://33333333-3333-4333-a333-333333333333"
    _remap_starting_topology_edge_endpoints(
        [pe],
        {old: "Only"},
        {"Only": new},
        workflow_name="TestWf",
        idx_wf=1,
    )
    assert pe.source == NodeId(new)
    assert pe.target is None


def test_remap_unknown_edge_endpoint_raises() -> None:
    missing_src = "node://99999999-9999-4999-a999-999999999999"
    edge = _edge(
        "edge://eeeeeeee-0000-4000-a000-e00000000003",
        missing_src,
        "node://bbbbbbbb-0000-4000-a000-000000000002",
    )
    new_b = "node://44444444-4444-4444-a444-444444444444"
    old_id_to_label = {"node://bbbbbbbb-0000-4000-a000-000000000002": "B"}
    label_to_new_id = {"B": new_b}
    with pytest.raises(ValueError, match="fatal catalog error"):
        _remap_starting_topology_edge_endpoints(
            [edge],
            old_id_to_label,
            label_to_new_id,
            workflow_name="TestWf",
            idx_wf=2,
        )


def test_require_unique_label_missing_raises() -> None:
    n = PartialBaseNode.model_validate(
        {
            "id": "node://aaaaaaaa-0000-4000-a000-000000000099",
            "operation": Operation.READ.value,
            "type": "customNode",
            "layer_index": 0,
        }
    )
    with pytest.raises(ValueError, match="no non-empty label"):
        _require_old_id_to_unique_label([n], workflow_name="BadWf", idx_wf=0)


def test_require_unique_label_duplicate_raises() -> None:
    a = _base_node("node://aaaaaaaa-0000-4000-a000-000000000001", "Same")
    b = _base_node("node://bbbbbbbb-0000-4000-a000-000000000002", "Same")
    with pytest.raises(ValueError, match="duplicate node label"):
        _require_old_id_to_unique_label([a, b], workflow_name="DupWf", idx_wf=0)
