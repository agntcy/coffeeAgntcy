# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Apply topology UI enrichment to workflow API response models."""

from __future__ import annotations

from typing import Any

from api.agentic_workflows.agent_ui_enrichment import enrich_topology_dict
from api.agentic_workflows.catalog_types import ChatApiTarget, chat_api_target_from_workflow
from api.agentic_workflows.transport_ui_enrichment import enrich_topology_transport
from schema.types import Workflow, WorkflowInstance


def _enrich_topology_payload(
    topology: dict[str, Any] | None,
    *,
    chat_api_target: ChatApiTarget | None,
) -> dict[str, Any]:
    enriched = enrich_topology_dict(topology)
    return enrich_topology_transport(enriched, chat_api_target=chat_api_target)


def enrich_workflow_topology(wf: Workflow) -> Workflow:
    data = wf.model_dump(mode="json")
    target = chat_api_target_from_workflow(wf)
    if isinstance(data.get("starting_topology"), dict):
        data["starting_topology"] = _enrich_topology_payload(
            data["starting_topology"],
            chat_api_target=target,
        )
    instances = data.get("instances")
    if isinstance(instances, dict):
        for inst in instances.values():
            if isinstance(inst, dict) and isinstance(inst.get("topology"), dict):
                inst["topology"] = _enrich_topology_payload(
                    inst["topology"],
                    chat_api_target=target,
                )
    return Workflow.model_validate(data)


def enrich_workflow_instance_topology(
    inst: WorkflowInstance,
    *,
    chat_api_target: ChatApiTarget | None = None,
) -> WorkflowInstance:
    data = inst.model_dump(mode="json")
    if isinstance(data.get("topology"), dict):
        data["topology"] = _enrich_topology_payload(
            data["topology"],
            chat_api_target=chat_api_target,
        )
    return WorkflowInstance.model_validate(data)
