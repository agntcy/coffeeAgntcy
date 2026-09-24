# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``common.workflow_utils.builders``."""

from __future__ import annotations

import logging

import pytest
from pydantic import ValidationError
from schema.types import (
    EventType,
    Operation,
    PartialAgentNode,
    PartialBaseNode,
    PartialTopology,
)

from common.workflow_utils.builders import (
    EVENT_SCHEMA_VERSION,
    build_event,
    build_metadata,
    make_edge,
    make_node,
)
from common.workflow_utils.node_types import (
    AGENT,
    CUSTOM_NODE,
    DIRECTORY,
    GROUP,
    MCP,
    TRANSPORT,
)
from common.workflow_utils.inflight import RuntimeIdAllocator
from common.workflow_utils.workflow_catalog import lookup_workflow


def test_schema_version_is_1_2_1():
    assert EVENT_SCHEMA_VERSION == "1.2.1"


@pytest.mark.parametrize(
    "case,stable_agent_id,expect_stable_fields,node_type,extras",
    [
        ("legacy_custom_node_without_extension", None, False, CUSTOM_NODE, None),
        (
            "legacy_custom_node_with_stable_agent_id",
            "agent://00000000-0000-4000-8000-000000000099",
            True,
            CUSTOM_NODE,
            None,
        ),
        (
            "type_agent_with_uri",
            None,
            False,
            AGENT,
            {"agent_record_uri": "agent-card://auction"},
        ),
        (
            "type_mcp_with_uri",
            None,
            False,
            MCP,
            {"agent_record_uri": "agent-card://weather-mcp"},
        ),
    ],
)
def test_make_node_stable_agent_fields(
    case, stable_agent_id, expect_stable_fields, node_type, extras
):
    """make_node optionally attaches stable_agent_id and agent_record_uri."""
    node = make_node(
        "node://00000000-0000-4000-8000-000000000001",
        operation=Operation.CREATE,
        node_type=node_type,
        label="Test Agent",
        layer_index=0,
        stable_agent_id=stable_agent_id,
        extras=extras,
    )
    assert node.label == "Test Agent"
    if extras and extras.get("agent_record_uri"):
        assert isinstance(node, PartialAgentNode)
        assert node.agent_record_uri == extras["agent_record_uri"]
        assert getattr(node, "stable_agent_id", None) is None
    elif expect_stable_fields:
        assert isinstance(node, PartialAgentNode)
        assert node.stable_agent_id.root == stable_agent_id
        assert (
            node.agent_record_uri == "agent-card://00000000-0000-4000-8000-000000000099"
        )
    else:
        assert isinstance(node, PartialBaseNode)
        assert getattr(node, "stable_agent_id", None) is None


@pytest.mark.parametrize(
    "case,node_type",
    [
        ("type_agent_without_extension", AGENT),
        ("type_mcp_without_extension", MCP),
    ],
)
def test_make_node_agent_extension_type_without_fields_raises(case, node_type):
    with pytest.raises(ValidationError):
        make_node(
            "node://00000000-0000-4000-8000-000000000001",
            operation=Operation.CREATE,
            node_type=node_type,
            label="Test Agent",
            layer_index=0,
        )


@pytest.mark.parametrize(
    "case,node_type,extras,stable_agent_id",
    [
        (
            "directory_with_uri_stays_base",
            DIRECTORY,
            {"agent_record_uri": "agent-card://directory"},
            None,
        ),
        (
            "transport_with_stable_id_stays_base",
            TRANSPORT,
            None,
            "agent://00000000-0000-4000-8000-000000000099",
        ),
        (
            "group_with_uri_stays_base",
            GROUP,
            {"agent_record_uri": "agent-card://group"},
            None,
        ),
    ],
)
def test_make_node_base_type_ignores_agent_fields(
    case, node_type, extras, stable_agent_id
):
    node = make_node(
        "node://00000000-0000-4000-8000-000000000001",
        operation=Operation.CREATE,
        node_type=node_type,
        label="Base Typed Node",
        layer_index=0,
        stable_agent_id=stable_agent_id,
        extras=extras,
    )
    assert isinstance(node, PartialBaseNode)
    assert getattr(node, "agent_record_uri", None) is None
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
    assert meta.schema_version == EVENT_SCHEMA_VERSION
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
    assert event.metadata.schema_version == EVENT_SCHEMA_VERSION


@pytest.mark.parametrize(
    "case,extras,stable_agent_id,expect_dropped_key",
    [
        (
            "kwarg_wins_over_extras_stable_id",
            {"stable_agent_id": "agent://00000000-0000-4000-8000-000000000088"},
            "agent://00000000-0000-4000-8000-000000000099",
            "stable_agent_id",
        ),
        (
            "extras_label_dropped",
            {"label": "From extras"},
            None,
            "label",
        ),
    ],
)
def test_make_node_drops_reserved_extras(
    caplog, case, extras, stable_agent_id, expect_dropped_key
):
    caplog.set_level(logging.WARNING)
    node = make_node(
        "node://00000000-0000-4000-8000-000000000001",
        operation=Operation.CREATE,
        node_type="customNode",
        label="Test Agent",
        layer_index=0,
        stable_agent_id=stable_agent_id,
        extras=extras,
    )
    assert node.label == "Test Agent"
    assert expect_dropped_key in caplog.text
    if stable_agent_id is not None:
        assert isinstance(node, PartialAgentNode)
        assert node.stable_agent_id.root == stable_agent_id
