# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Assign wire ``position`` to runtime-discovered topology nodes near their anchor.

Runs after :func:`reconcile_event_node_identities` and before
:func:`merge_event_data`. When the anchor node has a defined ``position``,
discovered agents (inline ``oasf_record`` agent dict on create) receive a
non-overlapping slot in a row beneath the anchor, using backend-only offset
constants. Slots are never reused or reshuffled, so agents found by a later
prompt extend the existing row instead of moving the ones already on screen.
When the anchor lacks ``position``, nodes are left unchanged so the frontend
auto-layout applies.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

from schema.types import Data, Event, Operation, Workflow

logger = logging.getLogger(__name__)

_DISCOVERY_LAYOUT_X_OFFSET = 285
_DISCOVERY_LAYOUT_Y_OFFSET = 185
_DISCOVERY_LAYOUT_MAX_ROWS = 20
# Counted per side, so a row holds 2 * N + 1 = 5 agents. Wider rows force the
# canvas to zoom out past the point where node labels are legible.
_DISCOVERY_LAYOUT_COLUMNS_PER_SIDE = 2


def _node_id(node: Any) -> str | None:
    nid = getattr(node, "id", None)
    if nid is None:
        return None
    root = getattr(nid, "root", None)
    if isinstance(root, str):
        return root
    return nid if isinstance(nid, str) else None


def _node_stable_agent_id(node: Any) -> str | None:
    sid = getattr(node, "stable_agent_id", None)
    if sid is None:
        return None
    root = getattr(sid, "root", None)
    if isinstance(root, str):
        return root
    return sid if isinstance(sid, str) else None


def _node_field(node: Any, key: str) -> Any:
    if hasattr(node, "model_dump"):
        return node.model_dump(mode="python").get(key)
    if isinstance(node, dict):
        return node.get(key)
    return getattr(node, key, None)


def _node_position(node: Any) -> tuple[float, float] | None:
    pos = _node_field(node, "position")
    if not isinstance(pos, dict):
        return None
    x = pos.get("x")
    y = pos.get("y")
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        return (float(x), float(y))
    return None


def _topology_nodes_for_instance(
    state_wf: Workflow | None,
    instance_id: str,
) -> list:
    if state_wf is None:
        return []
    inst = state_wf.instances.get(instance_id)
    if inst is not None and inst.topology is not None and inst.topology.nodes:
        return inst.topology.nodes
    if state_wf.starting_topology is not None and state_wf.starting_topology.nodes:
        return state_wf.starting_topology.nodes
    return []


def _is_discovered_create(node: Any) -> bool:
    op = getattr(node, "operation", None)
    if op != Operation.CREATE:
        return False
    if _node_position(node) is not None:
        return False
    record = _node_field(node, "oasf_record")
    return isinstance(record, dict)


def _anchor_id_for_target(edges: list | None, target_id: str) -> str | None:
    if not edges:
        return None
    for edge in edges:
        target = getattr(edge, "target", None)
        source = getattr(edge, "source", None)
        if target is None or source is None:
            continue
        target_root = getattr(target, "root", target)
        source_root = getattr(source, "root", source)
        if target_root == target_id and isinstance(source_root, str):
            return source_root
    return None


def _slot_is_free(
    cx: float,
    cy: float,
    occupied: list[tuple[float, float]],
    x_off: float,
    y_off: float,
) -> bool:
    for nx, ny in occupied:
        if abs(cx - nx) < x_off and abs(cy - ny) < y_off:
            return False
    return True


def _candidate_slots(
    anchor_x: float,
    anchor_y: float,
) -> Iterator[tuple[float, float]]:
    """Fill each row below the anchor, outward from its center, before dropping down.

    Discovered agents hang off the anchor's bottom handle, so a slot beside or
    above the anchor would draw an edge that leaves the bottom and doubles back.
    Widening the row keeps siblings on one line under their anchor.
    """
    for row in range(1, _DISCOVERY_LAYOUT_MAX_ROWS + 1):
        y = anchor_y + _DISCOVERY_LAYOUT_Y_OFFSET * row
        yield (anchor_x, y)
        for column in range(1, _DISCOVERY_LAYOUT_COLUMNS_PER_SIDE + 1):
            x_step = _DISCOVERY_LAYOUT_X_OFFSET * column
            yield (anchor_x + x_step, y)
            yield (anchor_x - x_step, y)


def _find_free_slot(
    anchor_x: float,
    anchor_y: float,
    occupied: list[tuple[float, float]],
) -> tuple[float, float] | None:
    for cx, cy in _candidate_slots(anchor_x, anchor_y):
        if _slot_is_free(
            cx,
            cy,
            occupied,
            _DISCOVERY_LAYOUT_X_OFFSET,
            _DISCOVERY_LAYOUT_Y_OFFSET,
        ):
            return (cx, cy)
    return None


def _occupied_positions(
    batch_occupied: list[tuple[str, float, float]],
    *,
    exclude_ids: set[str],
) -> list[tuple[float, float]]:
    return [(x, y) for node_id, x, y in batch_occupied if node_id not in exclude_ids]


def enrich_discovery_node_layout(state: Data, event: Event) -> Event:
    """Assign ``position`` to discovered create nodes when the anchor has one.

    Must run after :func:`reconcile_event_node_identities`. Returns a new
    :class:`Event`; the input is never mutated.
    """
    result = event.model_copy(deep=True)
    for wf_name, wf in result.data.workflows.items():
        state_wf = state.workflows.get(wf_name)
        for instance_id, inst in wf.instances.items():
            topology = inst.topology
            if topology is None or not topology.nodes:
                continue

            state_nodes = _topology_nodes_for_instance(state_wf, instance_id)
            node_by_id = {nid: node for node in state_nodes if (nid := _node_id(node))}

            batch_occupied: list[tuple[str, float, float]] = []
            for node in state_nodes:
                nid = _node_id(node)
                pos = _node_position(node)
                if nid is not None and pos is not None:
                    batch_occupied.append((nid, pos[0], pos[1]))

            target_to_source: dict[str, str] = {}
            for edge in topology.edges or []:
                target = getattr(edge, "target", None)
                source = getattr(edge, "source", None)
                if target is None or source is None:
                    continue
                target_root = getattr(target, "root", target)
                source_root = getattr(source, "root", source)
                if isinstance(target_root, str) and isinstance(source_root, str):
                    target_to_source[target_root] = source_root

            discovered = [
                node for node in topology.nodes if _is_discovered_create(node)
            ]
            discovered.sort(
                key=lambda n: (
                    _node_stable_agent_id(n) or "",
                    _node_id(n) or "",
                )
            )

            updates: dict[str, Any] = {}
            for node in discovered:
                node_id = _node_id(node)
                if node_id is None:
                    continue
                anchor_id = _anchor_id_for_target(topology.edges, node_id)
                if anchor_id is None:
                    continue
                anchor_node = node_by_id.get(anchor_id)
                if anchor_node is None:
                    continue
                anchor_pos = _node_position(anchor_node)
                if anchor_pos is None:
                    continue

                exclude_ids = {node_id, anchor_id}
                occupied = _occupied_positions(batch_occupied, exclude_ids=exclude_ids)
                slot = _find_free_slot(anchor_pos[0], anchor_pos[1], occupied)
                if slot is None:
                    # The node stays unpositioned and falls to frontend
                    # auto-layout, which cannot see the siblings placed here and
                    # may overlap them. Rare enough to leave as is, loud enough
                    # to explain a node that lands in the wrong place.
                    logger.warning(
                        "Discovery layout exhausted all %d slots under anchor %s; "
                        "leaving node %s unpositioned for frontend auto-layout.",
                        _DISCOVERY_LAYOUT_MAX_ROWS
                        * (2 * _DISCOVERY_LAYOUT_COLUMNS_PER_SIDE + 1),
                        anchor_id,
                        node_id,
                    )
                    continue

                cx, cy = slot
                updates[node_id] = node.model_copy(
                    update={"position": {"x": cx, "y": cy}}
                )
                batch_occupied.append((node_id, cx, cy))

            if not updates:
                continue

            topology.nodes = [
                updates[nid] if (nid := _node_id(node)) in updates else node
                for node in topology.nodes
            ]

    return result
