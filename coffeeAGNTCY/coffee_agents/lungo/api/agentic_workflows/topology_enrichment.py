# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Apply topology UI enrichment to workflow API response models."""

from __future__ import annotations

from api.agentic_workflows.agent_ui_enrichment import enrich_topology_dict
from schema.types import Workflow, WorkflowInstance


def enrich_workflow_topology(wf: Workflow) -> Workflow:
    data = wf.model_dump(mode="json")
    if isinstance(data.get("starting_topology"), dict):
        data["starting_topology"] = enrich_topology_dict(data["starting_topology"])
    instances = data.get("instances")
    if isinstance(instances, dict):
        for inst in instances.values():
            if isinstance(inst, dict) and isinstance(inst.get("topology"), dict):
                inst["topology"] = enrich_topology_dict(inst["topology"])
    return Workflow.model_validate(data)


def enrich_workflow_instance_topology(inst: WorkflowInstance) -> WorkflowInstance:
    data = inst.model_dump(mode="json")
    if isinstance(data.get("topology"), dict):
        data["topology"] = enrich_topology_dict(data["topology"])
    return WorkflowInstance.model_validate(data)
