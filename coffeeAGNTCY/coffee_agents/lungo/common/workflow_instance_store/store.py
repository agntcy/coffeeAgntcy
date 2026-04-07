# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""In-memory workflow-instance state store (#448).

Holds a merged ``data`` subtree (``workflows`` map) built from validated
``event_v1`` messages. No persistence, no URI generation. Invalid events do
not mutate state or invoke notifiers/subscribers.

Merges are synchronous; notifier and per-instance listeners run on a background
worker so slow callbacks do not block the next merge. Do not call :meth:`close`
from notifier or listener callbacks (deadlock risk).

See ``merge.py`` for merge semantics. Intended consumers: HTTP instance/state
API (#450), SSE (#451), A2A middleware (#452).
"""

from __future__ import annotations

import asyncio
import copy
import logging
import queue
import threading
import time
from collections import defaultdict
from typing import Callable, Final

from schema.validation import validate_data_against_schema

from common.workflow_instance_store.merge import merge_event_data
from common.workflow_instance_store.notifier import NoOpNotifier, NotifierProtocol

EVENT_SCHEMA = "event_v1"

logger = logging.getLogger(__name__)

_DISPATCH_SENTINEL: Final[object] = object()


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
        self._async_lock = asyncio.Lock()
        self._state_lock = threading.RLock()
        self._lifecycle_lock = threading.Lock()
        self._subscribers: dict[str, list[Callable[[dict], None]]] = defaultdict(
            list
        )
        self._closed = False
        self._dispatch_queue: queue.SimpleQueue[object] = queue.SimpleQueue()
        self._dispatch_cv = threading.Condition()
        self._outstanding_dispatches = 0
        self._worker_thread = threading.Thread(
            target=self._dispatch_loop,
            name="WorkflowInstanceStateStore-dispatch",
            daemon=True,
        )
        self._worker_thread.start()

    def close(self, timeout: float | None = 5.0) -> None:
        """Stop the dispatch worker. Idempotent. Do not call from notifier/listeners."""
        with self._lifecycle_lock:
            if self._worker_thread is None:
                return
            thread = self._worker_thread
            self._worker_thread = None
        with self._state_lock:
            self._closed = True
        self._dispatch_queue.put(_DISPATCH_SENTINEL)
        thread.join(timeout=timeout)
        if thread.is_alive():
            logger.warning(
                "WorkflowInstanceStateStore dispatch thread did not exit within %s s",
                timeout,
            )

    def wait_dispatch_idle(self, timeout: float | None = 5.0) -> None:
        """Block until all queued dispatch jobs finished (for tests / read-your-writes)."""
        end = None if timeout is None else time.monotonic() + timeout
        with self._dispatch_cv:
            while self._outstanding_dispatches > 0:
                if timeout is None:
                    self._dispatch_cv.wait()
                else:
                    remaining = end - time.monotonic()
                    if remaining <= 0:
                        msg = "Timed out waiting for dispatch queue to drain"
                        raise TimeoutError(msg)
                    if not self._dispatch_cv.wait(timeout=remaining):
                        msg = "Timed out waiting for dispatch queue to drain"
                        raise TimeoutError(msg)

    def get_merged_data(self) -> dict:
        """Deep copy of the accumulated ``data`` subtree."""
        with self._state_lock:
            return copy.deepcopy(self._snapshot)

    def get_instance_projection(
        self, workflow_key: str, instance_id: str
    ) -> dict | None:
        """Return workflow metadata plus the single instance, or ``None``."""
        with self._state_lock:
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

        with self._state_lock:
            self._subscribers[instance_id].append(listener)

        def unsubscribe() -> None:
            with self._state_lock:
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

    def _merge_snapshot(self, event: dict) -> list[str]:
        self._snapshot = merge_event_data(self._snapshot, event)
        return _touched_instance_ids(event)

    def _submit_core(self, work: dict) -> None:
        """Merge then enqueue dispatch. Lock is released before ``put`` so listeners can read state."""
        with self._state_lock:
            if self._closed:
                msg = "WorkflowInstanceStateStore is closed"
                raise RuntimeError(msg)
            touched = self._merge_snapshot(work)
        if not touched:
            return
        self._reject_if_closed()
        with self._dispatch_cv:
            self._outstanding_dispatches += 1
        self._dispatch_queue.put((tuple(touched), work))

    def _dispatch_loop(self) -> None:
        while True:
            job = self._dispatch_queue.get()
            if job is _DISPATCH_SENTINEL:
                break
            touched_ids, payload = job
            try:
                self._run_dispatch(touched_ids, payload)
            except Exception:
                logger.exception("WorkflowInstanceStateStore dispatch job failed")
            finally:
                with self._dispatch_cv:
                    self._outstanding_dispatches -= 1
                    self._dispatch_cv.notify_all()

    def _run_dispatch(
        self,
        touched_ids: tuple[str, ...],
        payload: dict,
    ) -> None:
        for iid in touched_ids:
            try:
                self._notifier.notify(iid, payload)
            except Exception:
                logger.exception(
                    "Notifier failed for instance_id=%s",
                    iid,
                )
        for iid in touched_ids:
            with self._state_lock:
                listeners = list(self._subscribers.get(iid, ()))
            for fn in listeners:
                try:
                    fn(payload)
                except Exception:
                    logger.exception(
                        "Subscriber failed for instance_id=%s",
                        iid,
                    )

    def _reject_if_closed(self) -> None:
        if self._closed:
            msg = "WorkflowInstanceStateStore is closed"
            raise RuntimeError(msg)

    def submit_event_sync(self, event: dict) -> None:
        """Validate, merge, then queue dispatch. Thread-safe for concurrent sync callers."""
        self._reject_if_closed()
        validate_data_against_schema(event, EVENT_SCHEMA)
        work = copy.deepcopy(event)
        self._submit_core(work)

    async def submit_event(self, event: dict) -> None:
        """Validate, merge, then queue dispatch. Serialized with an asyncio lock."""
        self._reject_if_closed()
        validate_data_against_schema(event, EVENT_SCHEMA)
        work = copy.deepcopy(event)
        async with self._async_lock:
            self._submit_core(work)
