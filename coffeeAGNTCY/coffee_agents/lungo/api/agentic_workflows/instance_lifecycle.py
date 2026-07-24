# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Helpers for workflow instance HTTP lifecycle (seed ``event_v1``, read merged state)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from common.workflow_instance_store.interfaces import WorkflowInstanceDataStore
from schema.types import Data, EventType, Workflow, WorkflowInstance

_EVENT_V1_SCHEMA_VERSION = "1.1.0"
_SEED_EVENT_SOURCE = "lungo.agentic_workflows.api"


def _new_event_id() -> str:
    return f"event://{uuid4()}"


def _new_correlation_id() -> str:
    return f"correlation://{uuid4()}"


def _metadata_timestamp_rfc3339_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_instantiate_seed_event(
    wf: Workflow,
    workflow_name: str,
    instance_uri: str,
) -> dict:
    """Build one validated ``event_v1`` payload that registers a new instance in the store."""
    if workflow_name != wf.name:
        msg = (
            f"workflow_name {workflow_name!r} must equal Workflow.name {wf.name!r} "
            "(catalog path key must match workflow definition)"
        )
        raise ValueError(msg)
    return {
        "metadata": {
            "timestamp": _metadata_timestamp_rfc3339_utc(),
            "schema_version": _EVENT_V1_SCHEMA_VERSION,
            "correlation": {"id": _new_correlation_id()},
            "id": _new_event_id(),
            "type": EventType.STATE_PROGRESS_UPDATE.value,
            "source": _SEED_EVENT_SOURCE,
        },
        "data": {
            "workflows": {
                workflow_name: {
                    "name": wf.name,
                    "pattern": wf.pattern,
                    "use_case": wf.use_case,
                    "scenario": wf.scenario,
                    "starting_topology": wf.starting_topology.model_dump(
                        mode="json",
                        exclude_none=True,
                    ),
                    "instances": {
                        instance_uri: {
                            "id": instance_uri,
                            "topology": {},
                        }
                    },
                }
            }
        },
    }


def instances_map_for_workflow(
    data: Data,
    workflow_name: str,
) -> dict[str, WorkflowInstance]:
    """Return a shallow copy of ``instances`` for ``workflow_name``, or ``{}`` if absent."""
    block = data.workflows.get(workflow_name)
    if block is None:
        return {}
    return dict(block.instances)


def workflow_instance_from_projection(
    projection: dict,
    instance_uri: str,
    *,
    topology_only: bool,
) -> WorkflowInstance:
    """Build a :class:`WorkflowInstance` response from :meth:`get_instance_projection` output."""
    raw_instances = projection.get("instances")
    if not isinstance(raw_instances, dict):
        msg = "projection missing instances map"
        raise ValueError(msg)
    inst_dict = raw_instances.get(instance_uri)
    if not isinstance(inst_dict, dict):
        msg = "projection missing instance entry"
        raise ValueError(msg)
    full = WorkflowInstance.model_validate(inst_dict)
    if topology_only:
        return WorkflowInstance(id=full.id, topology=full.topology)
    return full


def delete_workflow_instance_from_store(
    store: WorkflowInstanceDataStore,
    workflow_name: str,
    canonical_instance_uri: str,
) -> bool:
    """Remove one instance from the store; return False if workflow or instance missing."""
    return store.delete_instance(workflow_name, canonical_instance_uri)


def workflow_instance_from_store(
    store: WorkflowInstanceDataStore,
    workflow_key: str,
    instance_uri: str,
    *,
    topology_only: bool,
) -> WorkflowInstance | None:
    """Return one validated :class:`WorkflowInstance`, or ``None`` if missing.

    Reads via :meth:`~WorkflowInstanceDataStore.get_instance_projection` (one
    locked slice: workflow metadata plus the single instance) then
    :func:`workflow_instance_from_projection` — avoid :meth:`get_merged_data`
    for this path so the handler does not deep-copy the full merged graph.
    """
    proj = store.get_instance_projection(workflow_key, instance_uri)
    if proj is None:
        return None
    return workflow_instance_from_projection(
        proj, instance_uri, topology_only=topology_only
    )
