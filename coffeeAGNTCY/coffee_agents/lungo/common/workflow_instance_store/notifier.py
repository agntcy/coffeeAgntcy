# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Notifier protocol for workflow-instance state updates.

Each notification carries the full ``event_v1`` message as :class:`~schema.types.Event`
—the same payload #451 will serialize as one NDJSON line on SSE.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from schema.types import Event


@runtime_checkable
class NotifierProtocol(Protocol):
    def notify(self, instance_id: str, event: Event) -> None:
        """Called once per affected workflow instance after a successful merge."""


class NoOpNotifier:
    """Default notifier that performs no work."""

    def notify(self, instance_id: str, event: Event) -> None:  # noqa: ARG002
        return None
