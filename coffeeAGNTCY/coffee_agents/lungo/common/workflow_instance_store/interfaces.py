# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Narrow protocols for workflow-instance store (data vs fan-out)."""

from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable

from schema.types import Event, MergedData


@runtime_checkable
class WorkflowInstanceDataStore(Protocol):
    """Validate, enqueue, merge, and read accumulated ``MergedData``."""

    def submit_event_sync(self, event: dict) -> None:
        """Validate and enqueue an event (merge runs asynchronously)."""

    async def submit_event(self, event: dict) -> None:
        """Async validate and enqueue."""

    def get_merged_data(self) -> MergedData:
        """Deep copy of accumulated state."""

    def get_instance_projection(
        self, workflow_key: str, instance_id: str
    ) -> dict | None:
        """Workflow slice for one instance, or ``None``."""

    def wait_merge_idle(self, timeout: float | None = 5.0) -> None:
        """Block until all ingested events have been merged."""

    def close(self, timeout: float | None = 5.0) -> None:
        """Stop background workers."""


@runtime_checkable
class WorkflowInstanceEventFanout(Protocol):
    """Per-instance subscribers and post-merge dispatch idle."""

    def subscribe(
        self, instance_id: str, listener: Callable[[Event], None]
    ) -> Callable[[], None]:
        """Register a listener; returns unsubscribe."""

    def wait_dispatch_idle(self, timeout: float | None = 5.0) -> None:
        """Block until notifier/subscriber jobs have finished."""
