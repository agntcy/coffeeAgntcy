# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""In-memory workflow-instance state store (#448).

Holds a merged ``data`` subtree (``workflows`` map) built from validated
``event_v1`` messages. No persistence, no URI generation. Invalid events do
not mutate state or invoke notifiers/subscribers.

See ``merge.py`` for merge semantics. Intended consumers: HTTP instance/state
API (#450), SSE (#451), A2A middleware (#452).
"""

from __future__ import annotations

import asyncio
import copy
import threading
from collections import defaultdict
from typing import Callable

from schema.validation import validate_data_against_schema

from common.workflow_instance_store.merge import merge_event_data
from common.workflow_instance_store.notifier import NoOpNotifier, NotifierProtocol

EVENT_SCHEMA = "event_v1"


def _touched_instance_ids(event: dict) -> list[str]:
    data = event.get("data")
    if not isinstance(data, dict):
        return []
    workflows = data.get("workflows")
    if not isinstance(workflows, dict):
        return []
    seen: set[str] = set()
    ordered: list[str] = []
    for wf in workflows.values():
        if not isinstance(wf, dict):
            continue
        instances = wf.get("instances")
        if not isinstance(instances, dict):
            continue
        for iid in instances.keys():
            if isinstance(iid, str) and iid not in seen:
                seen.add(iid)
                ordered.append(iid)
    return ordered


class WorkflowInstanceStateStore:
    """Validate-then-merge store with optional notifier and per-instance subscribers."""

    def __init__(self, notifier: NotifierProtocol | None = None) -> None:
        self._notifier = notifier if notifier is not None else NoOpNotifier()
        self._snapshot: dict = {"workflows": {}}
        self._lock = asyncio.Lock()
        self._thread_lock = threading.Lock()
        self._subscribers: dict[str, list[Callable[[dict], None]]] = defaultdict(
            list
        )

    def get_merged_data(self) -> dict:
        """Deep copy of the accumulated ``data`` subtree."""
        return copy.deepcopy(self._snapshot)

    def get_instance_projection(
        self, workflow_key: str, instance_id: str
    ) -> dict | None:
        """Return workflow metadata plus the single instance, or ``None``."""
        wf = self._snapshot.get("workflows", {}).get(workflow_key)
        if not isinstance(wf, dict):
            return None
        instances = wf.get("instances")
        if not isinstance(instances, dict):
            return None
        inst = instances.get(instance_id)
        if not isinstance(inst, dict):
            return None
        return {
            "pattern": wf.get("pattern"),
            "use_case": wf.get("use_case"),
            "name": wf.get("name"),
            "starting_topology": copy.deepcopy(wf.get("starting_topology")),
            "instances": {instance_id: copy.deepcopy(inst)},
        }

    def subscribe(
        self, instance_id: str, listener: Callable[[dict], None]
    ) -> Callable[[], None]:
        """Register ``listener`` for successful events touching ``instance_id``."""

        self._subscribers[instance_id].append(listener)

        def unsubscribe() -> None:
            lst = self._subscribers.get(instance_id)
            if not lst:
                return
            try:
                lst.remove(listener)
            except ValueError:
                pass
            if not lst:
                del self._subscribers[instance_id]

        return unsubscribe

    def _apply_validated_event(self, event: dict) -> None:
        self._snapshot = merge_event_data(self._snapshot, event)
        touched = _touched_instance_ids(event)
        for iid in touched:
            self._notifier.notify(iid, event)
        for iid in touched:
            for fn in list(self._subscribers.get(iid, ())):
                fn(event)

    def submit_event_sync(self, event: dict) -> None:
        """Validate, then merge and notify. Thread-safe for concurrent sync callers."""
        validate_data_against_schema(event, EVENT_SCHEMA)
        with self._thread_lock:
            self._apply_validated_event(event)

    async def submit_event(self, event: dict) -> None:
        """Validate, then merge and notify. Serialized with an asyncio lock."""
        validate_data_against_schema(event, EVENT_SCHEMA)
        async with self._lock:
            with self._thread_lock:
                self._apply_validated_event(event)
