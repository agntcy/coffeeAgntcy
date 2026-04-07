# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Pure merge of ``event_v1`` ``data`` into an accumulated snapshot.

Store policy (not in JSON Schema): workflow and instance topology evolution.
Adjust here if product requirements change.

Topology node/edge items are interpreted **only** via ``operation``:
``create``, ``read``, ``update``, ``delete``.

**Node delete:** incident edges are **not** removed automatically (dangling
edges may remain until a later event removes them).

**``starting_topology``:** incoming replaces the snapshot only when the
incoming topology has at least one node or edge, or when the snapshot has no
non-empty ``starting_topology`` yet (initial empty placeholder from a prior
event is still replaced).

**Instance topology seeding:** when an instance has no nodes or edges yet,
``starting_topology`` on the same workflow snapshot (after merging the
current event's workflow fields) is copied as the base before applying the
instance ``topology`` delta, so ``update``-only instance payloads apply to the
expected graph.
"""

from __future__ import annotations

import copy
from typing import Any


def _stable_topology_list(by_id: dict[str, dict]) -> list[dict]:
    return [copy.deepcopy(by_id[k]) for k in sorted(by_id.keys())]


def _list_to_map(items: list[Any] | None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not items:
        return out
    for item in items:
        if not isinstance(item, dict):
            continue
        eid = item.get("id")
        if isinstance(eid, str):
            out[eid] = copy.deepcopy(item)
    return out


def _apply_topology_items(
    existing_nodes: dict[str, dict],
    existing_edges: dict[str, dict],
    items: list[Any] | None,
    *,
    kind: str,
) -> None:
    if not items:
        return
    bucket = existing_nodes if kind == "node" else existing_edges
    for raw in items:
        if not isinstance(raw, dict):
            continue
        op = raw.get("operation")
        eid = raw.get("id")
        if not isinstance(eid, str) or op not in (
            "create",
            "read",
            "update",
            "delete",
        ):
            continue
        match op:
            case "create" | "read":
                bucket[eid] = copy.deepcopy(raw)
            case "update":
                if eid not in bucket:
                    continue
                target = bucket[eid]
                for key, val in raw.items():
                    if key == "id":
                        continue
                    if isinstance(val, dict) and isinstance(target.get(key), dict):
                        target[key].update(val)
                    else:
                        target[key] = copy.deepcopy(val)
            case "delete":
                bucket.pop(eid, None)


def merge_topology_delta(
    existing_topology: dict,
    delta_topology: dict,
) -> dict:
    """Merge instance ``topology`` using per-item ``operation`` dispatch."""
    nodes_map = _list_to_map(existing_topology.get("nodes"))
    edges_map = _list_to_map(existing_topology.get("edges"))
    _apply_topology_items(
        nodes_map, edges_map, delta_topology.get("nodes"), kind="node"
    )
    _apply_topology_items(
        nodes_map, edges_map, delta_topology.get("edges"), kind="edge"
    )
    out: dict = {}
    if nodes_map:
        out["nodes"] = _stable_topology_list(nodes_map)
    else:
        out["nodes"] = []
    if edges_map:
        out["edges"] = _stable_topology_list(edges_map)
    else:
        out["edges"] = []
    for key, val in existing_topology.items():
        if key in ("nodes", "edges"):
            continue
        if key not in delta_topology:
            out[key] = copy.deepcopy(val)
    for key, val in delta_topology.items():
        if key in ("nodes", "edges"):
            continue
        out[key] = copy.deepcopy(val)
    return out


def _topology_has_entities(topology: dict) -> bool:
    nodes = topology.get("nodes")
    edges = topology.get("edges")
    return bool(nodes) or bool(edges)


def _merge_workflow(
    snapshot_wf: dict,
    incoming_wf: dict,
) -> None:
    for key in ("pattern", "use_case", "name"):
        if key in incoming_wf:
            snapshot_wf[key] = incoming_wf[key]
    if "starting_topology" in incoming_wf:
        st_in = incoming_wf["starting_topology"]
        if isinstance(st_in, dict):
            st_snap = snapshot_wf.get("starting_topology")
            if not isinstance(st_snap, dict):
                st_snap = {}
            if _topology_has_entities(st_in) or not _topology_has_entities(st_snap):
                snapshot_wf["starting_topology"] = copy.deepcopy(st_in)
    instances_in = incoming_wf.get("instances")
    if not isinstance(instances_in, dict):
        return
    instances_out = snapshot_wf.setdefault("instances", {})
    for map_key, inst_in in instances_in.items():
        if not isinstance(inst_in, dict):
            continue
        iid = inst_in.get("id", map_key)
        if not isinstance(iid, str):
            continue
        inst_out = instances_out.setdefault(iid, {"id": iid})
        inst_out["id"] = iid
        if "topology" in inst_in:
            base_topo = inst_out.get("topology")
            if not isinstance(base_topo, dict):
                base_topo = {}
            if not _topology_has_entities(base_topo):
                st = snapshot_wf.get("starting_topology")
                if isinstance(st, dict) and _topology_has_entities(st):
                    base_topo = copy.deepcopy(st)
            inst_out["topology"] = merge_topology_delta(
                base_topo,
                inst_in["topology"]
                if isinstance(inst_in["topology"], dict)
                else {},
            )
        for k, v in inst_in.items():
            if k in ("id", "topology"):
                continue
            inst_out[k] = copy.deepcopy(v)


def merge_event_data(existing_data: dict | None, event: dict) -> dict:
    """
    Merge ``event["data"]`` into ``existing_data`` (previous snapshot).

    ``event`` must be a full ``event_v1`` message; only ``data`` is read.
    """
    data_in = event.get("data")
    if not isinstance(data_in, dict):
        return copy.deepcopy(existing_data) if existing_data else {"workflows": {}}

    workflows_in = data_in.get("workflows")
    if not isinstance(workflows_in, dict):
        base = copy.deepcopy(existing_data) if existing_data else {}
        if "workflows" not in base:
            base["workflows"] = {}
        return base

    out = copy.deepcopy(existing_data) if existing_data else {}
    if "workflows" not in out:
        out["workflows"] = {}

    for wf_key, wf_in in workflows_in.items():
        if not isinstance(wf_in, dict):
            continue
        wf_out = out["workflows"].setdefault(wf_key, {})
        _merge_workflow(wf_out, wf_in)

    for key, val in data_in.items():
        if key == "workflows":
            continue
        out[key] = copy.deepcopy(val)

    return out
