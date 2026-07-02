# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Workflow instance state store (``event_v1`` merge + notifications)."""

from schema.types import Data

from common.workflow_instance_store.interfaces import (
    WorkflowInstanceDataStore,
    WorkflowInstanceEventFanout,
)
from common.workflow_instance_store.discovery_layout import enrich_discovery_node_layout
from common.workflow_instance_store.merge import (
    merge_event_data,
    merge_topology_delta,
    reconcile_event_node_identities,
)
from common.workflow_instance_store.notifier import NoOpNotifier, NotifierProtocol
from common.workflow_instance_store.errors import WorkflowInstanceStoreClosedError
from common.workflow_instance_store.store import WorkflowInstanceStateStore

__all__ = [
    "Data",
    "NoOpNotifier",
    "NotifierProtocol",
    "WorkflowInstanceDataStore",
    "WorkflowInstanceEventFanout",
    "WorkflowInstanceStateStore",
    "WorkflowInstanceStoreClosedError",
    "enrich_discovery_node_layout",
    "merge_event_data",
    "merge_topology_delta",
    "reconcile_event_node_identities",
]
