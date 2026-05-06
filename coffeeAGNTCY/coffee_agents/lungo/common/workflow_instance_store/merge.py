# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Pure merge of ``event_v1`` ``data`` into an accumulated snapshot.

Store policy (not in JSON Schema): workflow and instance topology evolution.
Adjust here if product requirements change.

Topology node/edge items are interpreted **only** via ``operation``:
``create``, ``read``, ``update``, ``delete``.

**``read``:** if an entity id already exists in the bucket, the snapshot is
unchanged for that id (read is not a write). If absent, the payload is stored
(establish / full representation).

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

**Topology list order:** ``nodes`` / ``edges`` lists follow **dict insertion
order** (merge encounter order), not lexicographic id order.

**Topology buckets:** applying node/edge deltas uses **pure** helpers: each step
returns a new id→entity map without mutating the previous map. Workflow-level
fields are still merged in place on a snapshot that ``merge_event_data`` has
already deep-copied.
"""

from __future__ import annotations

import copy
from typing import Any

from schema.types import Data, Event, Operation


def _topology_lists_insertion_order(by_id: dict[str, dict]) -> list[dict]:
    return [copy.deepcopy(by_id[k]) for k in by_id]


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


def _clone_topology_bucket(bucket: dict[str, dict]) -> dict[str, dict]:
    return {k: copy.deepcopy(v) for k, v in bucket.items()}


def _apply_one_topology_item(bucket: dict[str, dict], raw: dict) -> dict[str, dict]:
    """Return a new id→entity map after one node/edge item; *bucket* is not mutated."""
    op_raw = raw.get("operation")
    eid = raw.get("id")
    if not isinstance(eid, str):
        return bucket
    try:
        op = Operation(op_raw) if op_raw is not None else None
    except ValueError:
        return bucket
    match op:
        case Operation.CREATE:
            out = _clone_topology_bucket(bucket)
            out[eid] = copy.deepcopy(raw)
            return out
        case Operation.READ:
            if eid in bucket:
                return bucket
            out = _clone_topology_bucket(bucket)
            out[eid] = copy.deepcopy(raw)
            return out
        case Operation.UPDATE:
            if eid not in bucket:
                return bucket
            target = copy.deepcopy(bucket[eid])
            for key, val in raw.items():
                if key == "id":
                    continue
                if isinstance(val, dict) and isinstance(target.get(key), dict):
                    target[key] = {**target[key], **val}
                else:
                    target[key] = copy.deepcopy(val)
            out = {}
            for k, v in bucket.items():
                out[k] = target if k == eid else copy.deepcopy(v)
            return out
        case Operation.DELETE:
            if eid not in bucket:
                return bucket
            return {k: copy.deepcopy(v) for k, v in bucket.items() if k != eid}
        case _:
            return bucket


def _merge_topology_delta_maps(existing_topology: dict, delta_topology: dict) -> dict:
    """Merge topology maps and extra keys in one step (nodes + edges atomically).

    Node and edge buckets are reduced with :func:`_apply_one_topology_item` (pure fold).
    """
    nodes_map = _list_to_map(existing_topology.get("nodes"))
    edges_map = _list_to_map(existing_topology.get("edges"))
    for raw in delta_topology.get("nodes") or []:
        if isinstance(raw, dict):
            nodes_map = _apply_one_topology_item(nodes_map, raw)
    for raw in delta_topology.get("edges") or []:
        if isinstance(raw, dict):
            edges_map = _apply_one_topology_item(edges_map, raw)
    out: dict = {}
    out["nodes"] = _topology_lists_insertion_order(nodes_map)
    out["edges"] = _topology_lists_insertion_order(edges_map)
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


def merge_topology_delta(
    existing_topology: dict,
    delta_topology: dict,
) -> dict:
    """Merge instance ``topology`` using per-item ``operation`` dispatch.

    Returns a new topology dict; delta application does not mutate *existing_topology*.
    """
    return _merge_topology_delta_maps(existing_topology, delta_topology)


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


def merge_event_data(existing: Data | None, event: Event) -> Data:
    """
    Merge ``event.data`` into ``existing`` (previous snapshot).

    ``event`` must be a full ``event_v1`` message; only ``data`` is read.
    """
    data_in = event.data
    workflows_in = data_in.workflows

    existing_dict = (
        existing.model_dump(mode="python") if existing is not None else {"workflows": {}}
    )
    out = copy.deepcopy(existing_dict) if existing_dict else {}
    if "workflows" not in out:
        out["workflows"] = {}

    for wf_key, wf_in in workflows_in.items():
        wf_dump = wf_in.model_dump(mode="python", exclude_unset=True)
        wf_out = out["workflows"].setdefault(wf_key, {})
        _merge_workflow(wf_out, wf_dump)

    data_dump = data_in.model_dump(mode="python")
    for key, val in data_dump.items():
        if key == "workflows":
            continue
        out[key] = copy.deepcopy(val)

    return Data.model_validate(out)
