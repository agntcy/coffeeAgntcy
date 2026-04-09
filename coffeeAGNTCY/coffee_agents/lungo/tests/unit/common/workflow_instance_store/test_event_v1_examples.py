# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Packaged ``event_v1`` examples through the store + full validation (no HTTP)."""

from __future__ import annotations

from pathlib import Path

import pytest

from schema.json_schema import load_json_instance_file

from common.workflow_instance_store.store import WorkflowInstanceStateStore

_LUNGO_ROOT = Path(__file__).resolve().parents[4]
_EXAMPLES = _LUNGO_ROOT / "schema" / "jsonschemas" / "examples"


@pytest.mark.asyncio
async def test_submit_partial_example() -> None:
    data = load_json_instance_file(_EXAMPLES / "event_v1_partial.json")
    store = WorkflowInstanceStateStore()
    try:
        await store.submit_event(data)
        store.wait_merge_idle()
        merged = store.get_merged_data().model_dump(mode="python")
        wf = merged["workflows"]["recruiter"]
        inst_id = "instance://550e8400-e29b-41d4-a716-446655440003"
        assert inst_id in wf["instances"]
        assert wf["instances"][inst_id]["id"] == inst_id
        nodes = wf["instances"][inst_id]["topology"]["nodes"]
        labels = {n["id"]: n.get("label") for n in nodes}
        assert labels.get("node://550e8400-e29b-41d4-a716-446655440010") == "Auction Agent (search)"
    finally:
        store.close()


def test_submit_full_example_sync() -> None:
    data = load_json_instance_file(_EXAMPLES / "event_v1_full.json")
    store = WorkflowInstanceStateStore()
    try:
        store.submit_event_sync(data)
        store.wait_merge_idle()
        merged = store.get_merged_data().model_dump(mode="python")
        assert "recruiter" in merged["workflows"]
    finally:
        store.close()


def test_chain_partial_then_delta() -> None:
    partial = load_json_instance_file(_EXAMPLES / "event_v1_partial.json")
    store = WorkflowInstanceStateStore()
    try:
        store.submit_event_sync(partial)
        store.wait_merge_idle()
        delta = {
            "metadata": {
                "timestamp": "2026-01-02T00:00:00Z",
                "schema_version": "1.0.0",
                "correlation": {"id": "correlation://550e8400-e29b-41d4-a716-446655440001"},
                "id": "event://550e8400-e29b-41d4-a716-4466554400ff",
                "type": "StateProgressUpdate",
                "source": "test",
            },
            "data": {
                "workflows": {
                    "recruiter": {
                        "pattern": "recruiter_pattern",
                        "use_case": "hiring",
                        "name": "Recruiter",
                        "starting_topology": {"nodes": [], "edges": []},
                        "instances": {
                            "instance://550e8400-e29b-41d4-a716-446655440003": {
                                "id": "instance://550e8400-e29b-41d4-a716-446655440003",
                                "topology": {
                                    "nodes": [
                                        {
                                            "id": "node://550e8400-e29b-41d4-a716-446655440012",
                                            "operation": "update",
                                            "label": "Brazil Farm (updated)",
                                        }
                                    ],
                                },
                            }
                        },
                    }
                }
            },
        }
        store.submit_event_sync(delta)
        store.wait_merge_idle()
        inst = store.get_merged_data().model_dump(mode="python")["workflows"]["recruiter"][
            "instances"
        ]["instance://550e8400-e29b-41d4-a716-446655440003"]
        by_id = {n["id"]: n for n in inst["topology"]["nodes"]}
        assert (
            by_id["node://550e8400-e29b-41d4-a716-446655440012"]["label"]
            == "Brazil Farm (updated)"
        )
    finally:
        store.close()
