# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Errors for :class:`~common.workflow_instance_store.store.WorkflowInstanceStateStore`."""

from __future__ import annotations

_WORKFLOW_INSTANCE_STORE_CLOSED_MSG = "WorkflowInstanceStateStore is closed"


class WorkflowInstanceStoreClosedError(RuntimeError):
    """Raised when the store is closed or shutting down and the operation cannot proceed."""

    def __init__(self) -> None:
        super().__init__(_WORKFLOW_INSTANCE_STORE_CLOSED_MSG)
