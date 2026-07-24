# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for enrich_discovery_node_layout."""

from __future__ import annotations

from typing import Callable, NamedTuple

import pytest

from schema.types import Data, Event

from common.workflow_instance_store.discovery_layout import enrich_discovery_node_layout
from common.workflow_instance_store.merge import (
    merge_event_data,
    reconcile_event_node_identities,
)

INST = "instance://550e8400-e29b-41d4-a716-446655440003"
RECRUITER_RUNTIME_ID = "node://550e8400-e29b-41d4-a716-446655440100"
ANCHOR_ID = "node://550e8400-e29b-41d4-a716-446655440101"
DISCOVERED_ID = "node://550e8400-e29b-41d4-a716-446655440102"
DISCOVERED_ID_2 = "node://550e8400-e29b-41d4-a716-446655440103"
BLOCKER_ID = "node://550e8400-e29b-41d4-a716-446655440104"
RECRUITER_SID = "agent://550e8400-e29b-41d4-a716-446655440200"
DISCOVERED_SID = "agent://550e8400-e29b-41d4-a716-446655440202"
DISCOVERED_SID_2 = "agent://550e8400-e29b-41d4-a716-446655440203"
DISCOVERY_EDGE_ID = "edge://550e8400-e29b-41d4-a716-446655440300"
DISCOVERY_EDGE_ID_2 = "edge://550e8400-e29b-41d4-a716-446655440301"

RECRUITER_POSITION = {"x": 400, "y": 300}
DIRECTORY_POSITION = {"x": 800, "y": 100}
BELOW_SLOT = {"x": 400, "y": 485}
RIGHT_SLOT = {"x": 685, "y": 300}

_METADATA = {
    "timestamp": "2026-01-01T00:00:00Z",
    "schema_version": "1.0.0",
    "correlation": {"id": "correlation://550e8400-e29b-41d4-a716-446655440001"},
    "id": "event://550e8400-e29b-41d4-a716-446655440002",
    "type": "StateProgressUpdate",
    "source": "test",
}


def _evt(data: dict) -> Event:
    return Event.model_validate({"metadata": _METADATA, "data": data})


def _dump(m: Data) -> dict:
    return m.model_dump(mode="python")


def _recruiter_seed_node(*, with_position: bool = True) -> dict:
    node = {
        "id": RECRUITER_RUNTIME_ID,
        "operation": "create",
        "type": "customNode",
        "label": "Agentic Recruiter",
        "size": {"width": 1, "height": 1},
        "layer_index": 0,
        "stable_agent_id": RECRUITER_SID,
        "agent_record_uri": "agent-card://550e8400-e29b-41d4-a716-446655440200",
    }
    if with_position:
        node["position"] = dict(RECRUITER_POSITION)
    return node


def _directory_seed_node() -> dict:
    return {
        "id": "node://550e8400-e29b-41d4-a716-446655440099",
        "operation": "create",
        "type": "customNode",
        "label": "AGNTCY Agent Directory",
        "size": {"width": 1, "height": 1},
        "layer_index": 1,
        "position": dict(DIRECTORY_POSITION),
    }


def _discovered_node(
    node_id: str,
    stable_agent_id: str,
    *,
    label: str = "Brazil",
    cid: str = "cidB",
) -> dict:
    return {
        "id": node_id,
        "operation": "create",
        "type": "customNode",
        "label": label,
        "size": {"width": 1, "height": 1},
        "layer_index": 1,
        "stable_agent_id": stable_agent_id,
        "agent_record_uri": f"agent-card://{stable_agent_id.removeprefix('agent://')}",
        "oasf_record": {"name": label},
        "agent_cid": cid,
    }


def _discovery_topology_event(
    discovered_nodes: list[dict],
    edges: list[dict],
) -> Event:
    anchor = {
        "id": ANCHOR_ID,
        "operation": "create",
        "type": "customNode",
        "label": "Agentic Recruiter",
        "size": {"width": 1, "height": 1},
        "layer_index": 0,
        "stable_agent_id": RECRUITER_SID,
        "agent_record_uri": "agent-card://550e8400-e29b-41d4-a716-446655440200",
    }
    return _evt(
        {
            "workflows": {
                "w": {
                    "name": "n",
                    "pattern": "p",
                    "use_case": "u",
                    "scenario": "s",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        INST: {
                            "id": INST,
                            "topology": {
                                "nodes": [anchor, *discovered_nodes],
                                "edges": edges,
                            },
                        }
                    },
                }
            }
        }
    )


def _discovery_event() -> Event:
    discovered = _discovered_node(DISCOVERED_ID, DISCOVERED_SID)
    edge = {
        "id": DISCOVERY_EDGE_ID,
        "operation": "create",
        "type": "custom",
        "source": ANCHOR_ID,
        "target": DISCOVERED_ID,
        "bidirectional": False,
        "weight": 1.0,
    }
    return _discovery_topology_event([discovered], [edge])


def _wf_with_nodes(nodes: list[dict]) -> dict:
    return {
        "workflows": {
            "w": {
                "name": "n",
                "pattern": "p",
                "use_case": "u",
                "scenario": "s",
                "starting_topology": {"nodes": [], "edges": []},
                "instances": {
                    INST: {
                        "id": INST,
                        "topology": {"nodes": nodes, "edges": []},
                    }
                },
            }
        }
    }


def _state_recruiter_in_instance(*, with_position: bool = True) -> Data:
    return merge_event_data(
        None, _evt(_wf_with_nodes([_recruiter_seed_node(with_position=with_position)]))
    )


def _state_recruiter_in_starting_only(*, with_position: bool = True) -> Data:
    return Data.model_validate(
        {
            "workflows": {
                "w": {
                    "name": "n",
                    "pattern": "p",
                    "use_case": "u",
                    "scenario": "s",
                    "starting_topology": {
                        "nodes": [_recruiter_seed_node(with_position=with_position)],
                        "edges": [],
                    },
                    "instances": {
                        INST: {
                            "id": INST,
                            "topology": {"nodes": [], "edges": []},
                        }
                    },
                }
            }
        }
    )


def _discovered_position(event: Event) -> dict | None:
    topo = event.data.workflows["w"].instances[INST].topology
    for node in topo.nodes or []:
        if node.id.root == DISCOVERED_ID:
            dumped = node.model_dump(mode="python")
            pos = dumped.get("position")
            return pos if isinstance(pos, dict) else None
    return None


def _normalize_discovery(state: Data, event: Event) -> Event:
    reconciled = reconcile_event_node_identities(state, event)
    return enrich_discovery_node_layout(state, reconciled)


class LayoutStateCase(NamedTuple):
    case_id: str
    state_factory: Callable[..., Data]


_LAYOUT_STATE_CASES = (
    LayoutStateCase("recruiter_in_instance", _state_recruiter_in_instance),
    LayoutStateCase(
        "recruiter_in_starting_topology", _state_recruiter_in_starting_only
    ),
)


@pytest.mark.parametrize("case", _LAYOUT_STATE_CASES, ids=lambda c: c.case_id)
def test_enrich_assigns_below_anchor_when_anchor_has_position(case: LayoutStateCase):
    state = case.state_factory(with_position=True)
    enriched = _normalize_discovery(state, _discovery_event())
    assert _discovered_position(enriched) == BELOW_SLOT


def test_enrich_skips_position_when_anchor_has_no_position():
    state = _state_recruiter_in_instance(with_position=False)
    enriched = _normalize_discovery(state, _discovery_event())
    assert _discovered_position(enriched) is None


def test_enrich_uses_next_slot_when_below_is_blocked():
    blocker = {
        "id": BLOCKER_ID,
        "operation": "create",
        "type": "customNode",
        "label": "Blocker",
        "size": {"width": 1, "height": 1},
        "layer_index": 1,
        "position": dict(BELOW_SLOT),
    }
    state = merge_event_data(
        None, _evt(_wf_with_nodes([_recruiter_seed_node(), blocker]))
    )
    enriched = _normalize_discovery(state, _discovery_event())
    assert _discovered_position(enriched) == RIGHT_SLOT


def test_enrich_assigns_distinct_positions_for_two_discoveries():
    state = _state_recruiter_in_instance(with_position=True)
    discovered_a = _discovered_node(DISCOVERED_ID, DISCOVERED_SID, label="Brazil")
    discovered_b = _discovered_node(
        DISCOVERED_ID_2,
        DISCOVERED_SID_2,
        label="Colombia",
        cid="cidC",
    )
    edges = [
        {
            "id": DISCOVERY_EDGE_ID,
            "operation": "create",
            "type": "custom",
            "source": ANCHOR_ID,
            "target": DISCOVERED_ID,
            "bidirectional": False,
            "weight": 1.0,
        },
        {
            "id": DISCOVERY_EDGE_ID_2,
            "operation": "create",
            "type": "custom",
            "source": ANCHOR_ID,
            "target": DISCOVERED_ID_2,
            "bidirectional": False,
            "weight": 1.0,
        },
    ]
    event = _discovery_topology_event([discovered_a, discovered_b], edges)
    enriched = _normalize_discovery(state, event)
    topo = enriched.data.workflows["w"].instances[INST].topology
    positions = {
        node.id.root: node.model_dump(mode="python").get("position")
        for node in topo.nodes or []
        if node.id.root in {DISCOVERED_ID, DISCOVERED_ID_2}
    }
    assert positions[DISCOVERED_ID] == BELOW_SLOT
    assert positions[DISCOVERED_ID_2] == RIGHT_SLOT
    assert positions[DISCOVERED_ID] != positions[DISCOVERED_ID_2]


@pytest.mark.parametrize("case", _LAYOUT_STATE_CASES, ids=lambda c: c.case_id)
def test_reconcile_enrich_merge_retains_position(case: LayoutStateCase):
    state = case.state_factory(with_position=True)
    normalized = _normalize_discovery(state, _discovery_event())
    out = merge_event_data(state, normalized)
    topo = _dump(out)["workflows"]["w"]["instances"][INST]["topology"]
    discovered = next(n for n in topo["nodes"] if n["id"] == DISCOVERED_ID)
    assert discovered["position"] == BELOW_SLOT


def test_enrich_idempotent_on_reemit():
    state = _state_recruiter_in_instance(with_position=True)
    ev = _discovery_event()
    first = _normalize_discovery(state, ev)
    merged = merge_event_data(state, first)
    second = _normalize_discovery(merged, ev)
    assert _discovered_position(first) == _discovered_position(second)


def test_enrich_does_not_mutate_input_event():
    state = _state_recruiter_in_instance(with_position=True)
    ev = _discovery_event()
    enrich_discovery_node_layout(state, reconcile_event_node_identities(state, ev))
    assert _discovered_position(ev) is None


def test_enrich_with_directory_in_state_still_places_below_recruiter():
    state = merge_event_data(
        None,
        _evt(_wf_with_nodes([_recruiter_seed_node(), _directory_seed_node()])),
    )
    enriched = _normalize_discovery(state, _discovery_event())
    assert _discovered_position(enriched) == BELOW_SLOT
