# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for WorkflowInstanceStateStore."""

from __future__ import annotations

import asyncio
import threading

import pytest

from schema.errors import SchemaValidationError
from schema.types import Event

from common.workflow_instance_store import (
    WorkflowInstanceDataStore,
    WorkflowInstanceEventFanout,
    WorkflowInstanceStateStore,
)

_INSTANCE_KEY = "instance://550e8400-e29b-41d4-a716-446655440003"
_NODE = "node://550e8400-e29b-41d4-a716-446655440010"


def _minimal_valid_event() -> dict:
    return {
        "metadata": {
            "timestamp": "2026-01-01T00:00:00Z",
            "schema_version": "1.0.0",
            "correlation": {"id": "correlation://550e8400-e29b-41d4-a716-446655440001"},
            "id": "event://550e8400-e29b-41d4-a716-446655440002",
            "type": "StateProgressUpdate",
            "source": "test",
        },
        "data": {
            "workflows": {
                "w": {
                    "pattern": "p",
                    "use_case": "u",
                    "name": "n",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        _INSTANCE_KEY: {
                            "id": _INSTANCE_KEY,
                            "topology": {},
                        }
                    },
                }
            }
        },
    }


class RecordingNotifier:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Event]] = []

    def notify(self, instance_id: str, event: Event) -> None:
        self.calls.append((instance_id, event))


def test_store_implements_protocols() -> None:
    store = WorkflowInstanceStateStore()
    try:
        assert isinstance(store, WorkflowInstanceDataStore)
        assert isinstance(store, WorkflowInstanceEventFanout)
    finally:
        store.close()


def test_validation_failure_no_mutation_no_notifier():
    notifier = RecordingNotifier()
    store = WorkflowInstanceStateStore(notifier=notifier)
    try:
        good = _minimal_valid_event()
        store.submit_event_sync(good)
        store.wait_merge_idle()
        store.wait_dispatch_idle()
        before = store.get_merged_data()
        bad = {
            "metadata": good["metadata"],
            "data": {},
        }
        with pytest.raises(SchemaValidationError):
            store.submit_event_sync(bad)
        assert store.get_merged_data().model_dump(mode="json") == before.model_dump(
            mode="json"
        )
        assert len(notifier.calls) == 1
    finally:
        store.close()


def test_notifier_fanout_two_instances():
    notifier = RecordingNotifier()
    store = WorkflowInstanceStateStore(notifier=notifier)
    try:
        inst2 = "instance://550e8400-e29b-41d4-a716-446655440099"
        ev = {
            "metadata": {
                "timestamp": "2026-01-01T00:00:00Z",
                "schema_version": "1.0.0",
                "correlation": {"id": "correlation://550e8400-e29b-41d4-a716-446655440001"},
                "id": "event://550e8400-e29b-41d4-a716-446655440002",
                "type": "StateProgressUpdate",
                "source": "test",
            },
            "data": {
                "workflows": {
                    "w": {
                        "pattern": "p",
                        "use_case": "u",
                        "name": "n",
                        "starting_topology": {"nodes": [], "edges": []},
                        "instances": {
                            _INSTANCE_KEY: {
                                "id": _INSTANCE_KEY,
                                "topology": {},
                            },
                            inst2: {"id": inst2, "topology": {}},
                        },
                    }
                }
            },
        }
        expected = Event.model_validate(ev)
        store.submit_event_sync(ev)
        store.wait_merge_idle()
        store.wait_dispatch_idle()
        assert {c[0] for c in notifier.calls} == {_INSTANCE_KEY, inst2}
        assert notifier.calls[0][1].model_dump(mode="json") == expected.model_dump(
            mode="json"
        )
        assert notifier.calls[1][1].model_dump(mode="json") == expected.model_dump(
            mode="json"
        )
        assert notifier.calls[0][1] is not expected
    finally:
        store.close()


def test_subscribe_invoked_for_touching_instance_only():
    store = WorkflowInstanceStateStore()
    try:
        seen: list[str] = []

        def listener(_ev: Event) -> None:
            seen.append("x")

        unsub = store.subscribe(_INSTANCE_KEY, listener)
        store.submit_event_sync(_minimal_valid_event())
        store.wait_merge_idle()
        store.wait_dispatch_idle()
        assert seen == ["x"]
        other = "instance://550e8400-e29b-41d4-a716-446655440199"
        ev_other = {
            "metadata": _minimal_valid_event()["metadata"],
            "data": {
                "workflows": {
                    "w": {
                        "pattern": "p",
                        "use_case": "u",
                        "name": "n",
                        "starting_topology": {"nodes": [], "edges": []},
                        "instances": {
                            other: {"id": other, "topology": {}},
                        },
                    }
                }
            },
        }
        store.submit_event_sync(ev_other)
        store.wait_merge_idle()
        store.wait_dispatch_idle()
        assert seen == ["x"]
        unsub()
        store.submit_event_sync(_minimal_valid_event())
        store.wait_merge_idle()
        store.wait_dispatch_idle()
        assert seen == ["x"]
    finally:
        store.close()


@pytest.mark.asyncio
async def test_concurrent_submit_serializes_merges():
    store = WorkflowInstanceStateStore()
    try:
        seed = {
            "metadata": {
                "timestamp": "2026-01-01T00:00:00Z",
                "schema_version": "1.0.0",
                "correlation": {"id": "correlation://550e8400-e29b-41d4-a716-446655440001"},
                "id": "event://550e8400-e29b-41d4-a716-4466554400a0",
                "type": "StateProgressUpdate",
                "source": "test",
            },
            "data": {
                "workflows": {
                    "w": {
                        "pattern": "p",
                        "use_case": "u",
                        "name": "n",
                        "starting_topology": {"nodes": [], "edges": []},
                        "instances": {
                            _INSTANCE_KEY: {
                                "id": _INSTANCE_KEY,
                                "topology": {
                                    "nodes": [
                                        {
                                            "id": _NODE,
                                            "operation": "create",
                                            "type": "t",
                                            "label": "seed",
                                            "size": {"width": 1, "height": 1},
                                            "layer_index": 0,
                                        }
                                    ],
                                },
                            }
                        },
                    }
                }
            },
        }
        store.submit_event_sync(seed)
        store.wait_merge_idle()

        async def one(label: str, event_id: str) -> None:
            ev = {
                "metadata": {
                    "timestamp": "2026-01-01T00:00:00Z",
                    "schema_version": "1.0.0",
                    "correlation": {"id": "correlation://550e8400-e29b-41d4-a716-446655440001"},
                    "id": event_id,
                    "type": "StateProgressUpdate",
                    "source": "test",
                },
                "data": {
                    "workflows": {
                        "w": {
                            "pattern": "p",
                            "use_case": "u",
                            "name": "n",
                            "starting_topology": {"nodes": [], "edges": []},
                            "instances": {
                                _INSTANCE_KEY: {
                                    "id": _INSTANCE_KEY,
                                    "topology": {
                                        "nodes": [
                                            {
                                                "id": _NODE,
                                                "operation": "update",
                                                "label": label,
                                            }
                                        ],
                                    },
                                }
                            },
                        }
                    }
                },
            }
            await store.submit_event(ev)

        await asyncio.gather(
            one("first", "event://550e8400-e29b-41d4-a716-4466554400a1"),
            one("second", "event://550e8400-e29b-41d4-a716-4466554400a2"),
        )
        store.wait_merge_idle()
        nodes = store.get_merged_data().model_dump(mode="python")["workflows"]["w"][
            "instances"
        ][_INSTANCE_KEY]["topology"]["nodes"]
        assert len(nodes) == 1
        assert nodes[0]["label"] in ("first", "second")
    finally:
        store.close()


def test_concurrent_sync_submits_fifo_merge_order():
    store = WorkflowInstanceStateStore()
    try:
        seed = {
            "metadata": {
                "timestamp": "2026-01-01T00:00:00Z",
                "schema_version": "1.0.0",
                "correlation": {"id": "correlation://550e8400-e29b-41d4-a716-446655440001"},
                "id": "event://550e8400-e29b-41d4-a716-4466554400c0",
                "type": "StateProgressUpdate",
                "source": "test",
            },
            "data": {
                "workflows": {
                    "w": {
                        "pattern": "p",
                        "use_case": "u",
                        "name": "n",
                        "starting_topology": {"nodes": [], "edges": []},
                        "instances": {
                            _INSTANCE_KEY: {
                                "id": _INSTANCE_KEY,
                                "topology": {
                                    "nodes": [
                                        {
                                            "id": _NODE,
                                            "operation": "create",
                                            "type": "t",
                                            "label": "seed",
                                            "size": {"width": 1, "height": 1},
                                            "layer_index": 0,
                                        }
                                    ],
                                },
                            }
                        },
                    }
                }
            },
        }
        store.submit_event_sync(seed)
        store.wait_merge_idle()

        barrier = threading.Barrier(2)

        def push(label: str, eid: str) -> None:
            barrier.wait()
            ev = {
                "metadata": {
                    "timestamp": "2026-01-01T00:00:00Z",
                    "schema_version": "1.0.0",
                    "correlation": {"id": "correlation://550e8400-e29b-41d4-a716-446655440001"},
                    "id": eid,
                    "type": "StateProgressUpdate",
                    "source": "test",
                },
                "data": {
                    "workflows": {
                        "w": {
                            "pattern": "p",
                            "use_case": "u",
                            "name": "n",
                            "starting_topology": {"nodes": [], "edges": []},
                            "instances": {
                                _INSTANCE_KEY: {
                                    "id": _INSTANCE_KEY,
                                    "topology": {
                                        "nodes": [
                                            {
                                                "id": _NODE,
                                                "operation": "update",
                                                "label": label,
                                            }
                                        ],
                                    },
                                }
                            },
                        }
                    }
                },
            }
            store.submit_event_sync(ev)

        t1 = threading.Thread(
            target=push, args=("t1", "event://550e8400-e29b-41d4-a716-4466554400c1")
        )
        t2 = threading.Thread(
            target=push, args=("t2", "event://550e8400-e29b-41d4-a716-4466554400c2")
        )
        t1.start()
        t2.start()
        t1.join(timeout=10.0)
        t2.join(timeout=10.0)
        store.wait_merge_idle()
        final_label = store.get_merged_data().model_dump(mode="python")["workflows"]["w"][
            "instances"
        ][_INSTANCE_KEY]["topology"]["nodes"][0]["label"]
        assert final_label in ("t1", "t2")
    finally:
        store.close()


def test_get_instance_projection():
    store = WorkflowInstanceStateStore()
    try:
        store.submit_event_sync(_minimal_valid_event())
        store.wait_merge_idle()
        proj = store.get_instance_projection("w", _INSTANCE_KEY)
        assert proj is not None
        assert proj["instances"][_INSTANCE_KEY]["id"] == _INSTANCE_KEY
        assert store.get_instance_projection("missing", _INSTANCE_KEY) is None
    finally:
        store.close()


def test_slow_notifier_does_not_block_merge():
    entered = threading.Event()
    hold = threading.Event()
    th: threading.Thread | None = None

    class GateNotifier:
        def notify(self, instance_id: str, event: Event) -> None:
            entered.set()
            assert hold.wait(timeout=30), "notifier hold timed out"

    store = WorkflowInstanceStateStore(notifier=GateNotifier())
    try:
        ev1 = _minimal_valid_event()
        ev2 = {
            "metadata": {
                "timestamp": "2026-01-01T00:00:01Z",
                "schema_version": "1.0.0",
                "correlation": {"id": "correlation://550e8400-e29b-41d4-a716-446655440001"},
                "id": "event://550e8400-e29b-41d4-a716-4466554400b1",
                "type": "StateProgressUpdate",
                "source": "test",
            },
            "data": {
                "workflows": {
                    "w": {
                        "pattern": "p2",
                        "use_case": "u2",
                        "name": "n2",
                        "starting_topology": {"nodes": [], "edges": []},
                        "instances": {
                            _INSTANCE_KEY: {
                                "id": _INSTANCE_KEY,
                                "topology": {},
                            }
                        },
                    }
                }
            },
        }

        def first_submit() -> None:
            store.submit_event_sync(ev1)

        th = threading.Thread(target=first_submit)
        th.start()
        assert entered.wait(timeout=2.0)
        store.submit_event_sync(ev2)
        store.wait_merge_idle()
        assert (
            store.get_merged_data().model_dump(mode="python")["workflows"]["w"]["pattern"]
            == "p2"
        )
        hold.set()
        th.join(timeout=2.0)
        assert not th.is_alive()
        store.wait_dispatch_idle()
    finally:
        hold.set()
        if th is not None:
            th.join(timeout=2.0)
        store.close()


def test_close_rejects_submits():
    store = WorkflowInstanceStateStore()
    store.close()
    with pytest.raises(RuntimeError, match="closed"):
        store.submit_event_sync(_minimal_valid_event())


@pytest.mark.asyncio
async def test_close_rejects_async_submit():
    store = WorkflowInstanceStateStore()
    store.close()
    with pytest.raises(RuntimeError, match="closed"):
        await store.submit_event(_minimal_valid_event())


def test_wait_dispatch_idle_rejects_when_closed():
    store = WorkflowInstanceStateStore()
    store.close()
    with pytest.raises(RuntimeError, match="closed"):
        store.wait_dispatch_idle()


def test_wait_merge_idle_rejects_when_closed():
    store = WorkflowInstanceStateStore()
    store.close()
    with pytest.raises(RuntimeError, match="closed"):
        store.wait_merge_idle()


def test_close_idempotent():
    store = WorkflowInstanceStateStore()
    store.close()
    store.close()
