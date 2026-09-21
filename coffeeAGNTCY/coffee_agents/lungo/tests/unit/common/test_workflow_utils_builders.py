# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``common.workflow_utils.builders``."""

from __future__ import annotations

import pytest
from schema.types import (
    EventType,
    Operation,
    PartialAgentNode,
    PartialBaseNode,
    PartialTopology,
)

from common.workflow_utils.builders import (
    SCHEMA_VERSION,
    build_event,
    build_metadata,
    make_edge,
    make_node,
)
from common.workflow_utils.inflight import RuntimeIdAllocator
from common.workflow_utils.workflow_catalog import lookup_workflow


@pytest.mark.parametrize(
    "case,stable_agent_id,expect_stable_fields",
    [
        ("without_stable_agent_id", None, False),
        ("with_stable_agent_id", "agent://00000000-0000-4000-8000-000000000099", True),
    ],
)
def test_make_node_stable_agent_fields(case, stable_agent_id, expect_stable_fields):
    """make_node optionally attaches stable_agent_id and agent_record_uri."""
    node = make_node(
        "node://00000000-0000-4000-8000-000000000001",
        operation=Operation.CREATE,
        node_type="customNode",
        label="Test Agent",
        layer_index=0,
        stable_agent_id=stable_agent_id,
    )
    assert node.label == "Test Agent"
    if expect_stable_fields:
        assert isinstance(node, PartialAgentNode)
        assert node.stable_agent_id.root == stable_agent_id
        assert node.agent_record_uri == "agent-card://00000000-0000-4000-8000-000000000099"
    else:
        assert isinstance(node, PartialBaseNode)
        assert getattr(node, "stable_agent_id", None) is None


@pytest.mark.parametrize(
    "case,trace_id,span_id,expect_trace,expect_span",
    [
        ("trace_and_span", 0xABC, 0xDEF, True, True),
        ("trace_only", 0xABC, None, True, False),
        ("neither", None, None, False, False),
    ],
)
def test_build_metadata_otel_fields(case, trace_id, span_id, expect_trace, expect_span):
    """build_metadata embeds hex trace/span ids when provided."""
    meta = build_metadata(
        source="test_source",
        event_type=EventType.STATE_PROGRESS_UPDATE,
        correlation_id="correlation://00000000-0000-4000-8000-000000000002",
        trace_id=trace_id,
        span_id=span_id,
    )
    assert meta.schema_version == SCHEMA_VERSION
    if expect_trace:
        assert getattr(meta, "trace_id", None) == f"{trace_id:032x}"
    else:
        assert getattr(meta, "trace_id", None) is None
    if expect_span:
        assert getattr(meta, "span_id", None) == f"{span_id:016x}"
    else:
        assert getattr(meta, "span_id", None) is None


def test_build_event_happy_path():
    """build_event resolves catalog metadata and embeds topology."""
    metadata = lookup_workflow("Test Workflow Alpha")
    assert metadata is not None

    event = build_event(
        source="test_source",
        identity=metadata,
        instance_id="instance://00000000-0000-4000-8000-000000000003",
        topology=PartialTopology(nodes=[], edges=[]),
        correlation_id="correlation://00000000-0000-4000-8000-000000000004",
    )
    wf = event.data.workflows["Test Workflow Alpha"]
    assert wf.pattern == metadata.pattern
    assert wf.use_case == metadata.use_case
    instance = next(iter(wf.instances.values()))
    assert instance.topology.nodes == []


@pytest.mark.parametrize(
    "case,operation,expect_weight_in_dump,expect_bidirectional_in_dump",
    [
        ("create_sets_defaults", Operation.CREATE, True, True),
        ("update_omits_create_fields", Operation.UPDATE, False, False),
    ],
)
@pytest.mark.asyncio
async def test_make_edge_create_vs_update(
    case, operation, expect_weight_in_dump, expect_bidirectional_in_dump
):
    """make_edge passes weight/bidirectional only on CREATE (exclude_unset)."""
    allocator = RuntimeIdAllocator()
    source = "node://00000000-0000-4000-8000-000000000010"
    target = "node://00000000-0000-4000-8000-000000000011"
    edge = await make_edge(
        source,
        target,
        operation=operation,
        allocator=allocator,
    )
    assert edge.source.root == source
    assert edge.target.root == target
    assert edge.operation == operation
    dump = edge.model_dump(exclude_unset=True)
    assert ("weight" in dump) is expect_weight_in_dump
    assert ("bidirectional" in dump) is expect_bidirectional_in_dump


def test_build_event_writes_identity_name():
    """build_event keys the workflow map with identity.name."""
    metadata = lookup_workflow("Test Workflow Alpha")
    assert metadata is not None
    event = build_event(
        source="test_source",
        identity=metadata,
        instance_id="instance://00000000-0000-4000-8000-000000000003",
        topology=PartialTopology(nodes=[], edges=[]),
        correlation_id="correlation://00000000-0000-4000-8000-000000000004",
    )
    assert metadata.name in event.data.workflows
    assert event.metadata.schema_version == SCHEMA_VERSION
