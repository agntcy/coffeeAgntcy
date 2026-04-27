# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""In-memory workflow-instance state store (#448).

Holds a merged ``Data`` snapshot built from validated ``event_v1``
messages. **Submit** paths validate and enqueue; a **merge worker** applies
merges in FIFO order; a **dispatch worker** runs notifier and per-instance
listeners so slow callbacks do not block merging.

Events with ``data.workflows`` empty still merge into the snapshot (including
any extra keys on ``data`` allowed by the schema). Dispatch runs only when the
event touches at least one workflow instance; otherwise listeners are not
invoked. Use :meth:`get_merged_data` to read the merged snapshot, including
non-workflow fields on ``data``.

**Read-your-writes:** after :meth:`submit_event_sync` / :meth:`submit_event`,
call :meth:`wait_merge_idle` before reading :meth:`get_merged_data` if you
need the merged snapshot. Use :meth:`wait_dispatch_idle` when notifier /
subscriber ordering matters.

Do not call :meth:`close` from notifier or listener callbacks (deadlock risk).

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

from schema.types import Data, Event
from schema.validation import validate_data_against_schema

from common.workflow_instance_store.merge import merge_event_data
from common.workflow_instance_store.notifier import NoOpNotifier, NotifierProtocol

EVENT_SCHEMA = "event_v1"

_STORE_CLOSED_MSG = "WorkflowInstanceStateStore is closed"

logger = logging.getLogger(__name__)

_MERGE_SENTINEL: Final[object] = object()
_DISPATCH_SENTINEL: Final[object] = object()


def _touched_instance_ids(event: Event) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for wf in event.data.workflows.values():
        for iid in wf.instances:
            if iid not in seen:
                seen.add(iid)
                ordered.append(iid)
    return ordered


class _MergeCoordinator:
    """Ingest queue + merge worker: owns applying ``merge_event_data`` under ``_state_lock``."""

    __slots__ = (
        "_ingest_queue",
        "_merge_cv",
        "_merge_thread",
        "_on_merged",
        "_pending_merge",
        "_state",
        "_state_lock",
    )

    def __init__(
        self,
        state_lock: threading.RLock,
        initial_state: Data,
        on_merged: Callable[[Event, list[str]], None],
    ) -> None:
        self._state_lock = state_lock
        self._state = initial_state
        self._on_merged = on_merged
        self._ingest_queue: queue.SimpleQueue[object] = queue.SimpleQueue()
        self._merge_cv = threading.Condition()
        self._pending_merge = 0
        self._merge_thread = threading.Thread(
            target=self._merge_loop,
            name="WorkflowInstanceStateStore-merge",
            daemon=True,
        )
        self._merge_thread.start()

    @property
    def state(self) -> Data:
        return self._state

    @state.setter
    def state(self, v: Data) -> None:
        self._state = v

    def enqueue(self, work: Event) -> None:
        with self._merge_cv:
            self._pending_merge += 1
        self._ingest_queue.put(work)

    def close(self, timeout: float | None) -> None:
        self._ingest_queue.put(_MERGE_SENTINEL)
        self._merge_thread.join(timeout=timeout)
        if self._merge_thread.is_alive():
            logger.warning(
                "WorkflowInstanceStateStore merge thread did not exit within %s s",
                timeout,
            )

    def wait_merge_idle(self, timeout: float | None) -> None:
        end = None if timeout is None else time.monotonic() + timeout
        with self._merge_cv:
            while self._pending_merge > 0:
                if timeout is None:
                    self._merge_cv.wait()
                else:
                    remaining = end - time.monotonic()
                    if remaining <= 0 or not self._merge_cv.wait(timeout=remaining):
                        msg = "Timed out waiting for merge queue to drain"
                        raise TimeoutError(msg)

    def _merge_loop(self) -> None:
        while True:
            item = self._ingest_queue.get()
            if item is _MERGE_SENTINEL:
                break
            assert isinstance(item, Event)
            try:
                touched = _touched_instance_ids(item)
                with self._state_lock:
                    self._state = merge_event_data(self._state, item)
                if touched:
                    self._on_merged(item, touched)
            except Exception:
                logger.exception("WorkflowInstanceStateStore merge worker failed")
            finally:
                with self._merge_cv:
                    self._pending_merge -= 1
                    self._merge_cv.notify_all()


class _DispatchHub:
    """Dispatch queue + worker: notifier and per-instance listeners."""

    __slots__ = (
        "_dispatch_cv",
        "_dispatch_queue",
        "_dispatch_thread",
        "_notifier",
        "_outstanding_dispatches",
        "_state_lock",
        "_subscribers",
    )

    def __init__(
        self,
        state_lock: threading.RLock,
        notifier: NotifierProtocol,
    ) -> None:
        self._state_lock = state_lock
        self._notifier = notifier
        self._subscribers: dict[str, list[Callable[[Event], None]]] = defaultdict(
            list
        )
        self._dispatch_queue: queue.SimpleQueue[object] = queue.SimpleQueue()
        self._dispatch_cv = threading.Condition()
        self._outstanding_dispatches = 0
        self._dispatch_thread = threading.Thread(
            target=self._dispatch_loop,
            name="WorkflowInstanceStateStore-dispatch",
            daemon=True,
        )
        self._dispatch_thread.start()

    @property
    def notifier(self) -> NotifierProtocol:
        return self._notifier

    def subscribe(
        self, instance_id: str, listener: Callable[[Event], None]
    ) -> Callable[[], None]:
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

    def enqueue_dispatch(self, touched: list[str], payload: Event) -> None:
        with self._dispatch_cv:
            self._outstanding_dispatches += 1
        self._dispatch_queue.put((tuple(touched), payload))

    def wait_dispatch_idle(self, timeout: float | None) -> None:
        end = None if timeout is None else time.monotonic() + timeout
        with self._dispatch_cv:
            while self._outstanding_dispatches > 0:
                if timeout is None:
                    self._dispatch_cv.wait()
                else:
                    remaining = end - time.monotonic()
                    if remaining <= 0 or not self._dispatch_cv.wait(
                        timeout=remaining
                    ):
                        msg = "Timed out waiting for dispatch queue to drain"
                        raise TimeoutError(msg)

    def close(self, timeout: float | None) -> None:
        self._dispatch_queue.put(_DISPATCH_SENTINEL)
        self._dispatch_thread.join(timeout=timeout)
        if self._dispatch_thread.is_alive():
            logger.warning(
                "WorkflowInstanceStateStore dispatch thread did not exit within %s s",
                timeout,
            )

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
        payload: Event,
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


class WorkflowInstanceStateStore:
    """Validate-then-enqueue store with optional notifier and per-instance subscribers."""

    def __init__(self, notifier: NotifierProtocol | None = None) -> None:
        self._lifecycle_lock = threading.Lock()
        self._running = True
        self._state_lock = threading.RLock()
        self._closed = False
        n = notifier if notifier is not None else NoOpNotifier()
        self._dispatch = _DispatchHub(self._state_lock, n)
        self._merge = _MergeCoordinator(
            self._state_lock,
            Data(),
            self._after_merge_enqueue_dispatch,
        )

    def _after_merge_enqueue_dispatch(self, item: Event, touched: list[str]) -> None:
        self._dispatch.enqueue_dispatch(touched, item.model_copy(deep=True))

    def close(self, timeout: float | None = 5.0) -> None:
        """Stop merge and dispatch workers. Idempotent."""
        with self._lifecycle_lock:
            if not self._running:
                return
            self._running = False
        with self._state_lock:
            self._closed = True
        self._merge.close(timeout=timeout)
        self._dispatch.close(timeout=timeout)

    def wait_merge_idle(self, timeout: float | None = 5.0) -> None:
        """Block until all ingested events have been merged.

        Raises ``RuntimeError`` if the store is already :meth:`close`d.
        """
        with self._state_lock:
            if self._closed:
                raise RuntimeError(_STORE_CLOSED_MSG)
        self._merge.wait_merge_idle(timeout=timeout)

    def wait_dispatch_idle(self, timeout: float | None = 5.0) -> None:
        """Block until all queued dispatch jobs finished.

        Raises ``RuntimeError`` if the store is already :meth:`close`d.
        """
        with self._state_lock:
            if self._closed:
                raise RuntimeError(_STORE_CLOSED_MSG)
        self._dispatch.wait_dispatch_idle(timeout=timeout)

    def get_merged_data(self) -> Data:
        """Deep copy of the accumulated merged ``data`` subtree."""
        with self._state_lock:
            return self._merge.state.model_copy(deep=True)

    def get_instance_projection(
        self, workflow_key: str, instance_id: str
    ) -> dict | None:
        """Return workflow metadata plus the single instance, or ``None``."""
        with self._state_lock:
            snap = self._merge.state.model_dump(mode="python")
            wf = snap.get("workflows", {}).get(workflow_key)
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
        self, instance_id: str, listener: Callable[[Event], None]
    ) -> Callable[[], None]:
        """Register ``listener`` for successful events touching ``instance_id``."""
        return self._dispatch.subscribe(instance_id, listener)

    def submit_event_sync(self, event: dict) -> None:
        """Validate and enqueue; merge runs on the merge worker thread."""
        with self._lifecycle_lock:
            if not self._running:
                raise RuntimeError(_STORE_CLOSED_MSG)
            validate_data_against_schema(event, EVENT_SCHEMA)
            work = Event.model_validate(event)
            self._merge.enqueue(work)

    async def submit_event(self, event: dict) -> None:
        """Validate and enqueue without blocking the event loop on merge."""

        def _submit() -> None:
            with self._lifecycle_lock:
                if not self._running:
                    raise RuntimeError(_STORE_CLOSED_MSG)
                validate_data_against_schema(event, EVENT_SCHEMA)
                work = Event.model_validate(event)
                self._merge.enqueue(work)

        await asyncio.to_thread(_submit)
