# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Load and validate the catalog of starting workflows.

Validates ``starting_workflows.json`` against the ``Workflow`` Pydantic model
and exposes the validated workflow definitions for use by other modules.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from threading import Lock
from uuid import uuid4

import httpx
from pydantic import ValidationError

from api.agentic_workflows.agent_ui_enrichment import register_from_record
from common.stable_agent_id import stable_agent_uuid_for_name
from schema.types import (
    AgentNode,
    Edge,
    NodeId,
    PartialAgentNode,
    PartialEdge,
    TopologyEdgeItem,
    TopologyNodeItem,
    Workflow,
    edge_id_from_uuid,
    node_id_from_uuid,
    stable_agent_id_from_uuid,
)


logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent
_STARTING_WORKFLOWS_FILE = _DATA_DIR / "starting_workflows.json"

# Mapping of workflow name to validated Workflow model.
_STARTING_WORKFLOWS: dict[str, Workflow] | None = None

# This is a global lock to ensure that the starting workflows are initialized only once.
_INIT_LOCK = Lock()
_INITIALIZED = False


def _node_edge_remap_label(node: TopologyNodeItem) -> str | None:
    """Return a non-empty display label if the node carries one, else None."""
    raw = getattr(node, "label", None)
    if raw is None:
        return None
    value = raw.root if hasattr(raw, "root") else raw
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _require_old_id_to_unique_label(
    nodes: list[TopologyNodeItem],
    *,
    workflow_name: str,
    idx_wf: int,
) -> dict[str, str]:
    """Build ``old_node_id -> label``; every node must have a unique non-empty label."""
    old_id_to_label: dict[str, str] = {}
    label_to_old_id: dict[str, str] = {}
    for idx_nd, node in enumerate(nodes):
        old_id = node.id.root
        label = _node_edge_remap_label(node)
        if not label:
            raise ValueError(
                f"Starting workflow {workflow_name!r} (index {idx_wf}): fatal catalog error — "
                f"topology node at index {idx_nd} (id {old_id!r}) has no non-empty label; "
                "labels are required to remap edges after runtime node ids are assigned."
            )
        if label in label_to_old_id:
            first_old = label_to_old_id[label]
            raise ValueError(
                f"Starting workflow {workflow_name!r} (index {idx_wf}): fatal catalog error — "
                f"duplicate node label {label!r} (node ids {first_old!r} and {old_id!r})."
            )
        label_to_old_id[label] = old_id
        old_id_to_label[old_id] = label
    return old_id_to_label


def _remap_starting_topology_edge_endpoints(
    edges: list[TopologyEdgeItem],
    old_id_to_label: dict[str, str],
    label_to_new_id: dict[str, str],
    *,
    workflow_name: str,
    idx_wf: int,
) -> None:
    """Rewrite edge ``source`` / ``target`` using node labels after new ids were assigned."""
    for idx_e, edge in enumerate(edges):
        if isinstance(edge, PartialEdge):
            if edge.source is not None:
                old = edge.source.root
                lab = old_id_to_label.get(old)
                if lab is None:
                    raise ValueError(
                        f"Starting workflow {workflow_name!r} (index {idx_wf}): fatal catalog error — "
                        f"PartialEdge at index {idx_e} references unknown source node id {old!r}."
                    )
                new = label_to_new_id.get(lab)
                if new is None:
                    raise ValueError(
                        f"Starting workflow {workflow_name!r} (index {idx_wf}): fatal catalog error — "
                        f"PartialEdge at index {idx_e} source label {lab!r} has no new node id."
                    )
                edge.source = NodeId(new)
            if edge.target is not None:
                old = edge.target.root
                lab = old_id_to_label.get(old)
                if lab is None:
                    raise ValueError(
                        f"Starting workflow {workflow_name!r} (index {idx_wf}): fatal catalog error — "
                        f"PartialEdge at index {idx_e} references unknown target node id {old!r}."
                    )
                new = label_to_new_id.get(lab)
                if new is None:
                    raise ValueError(
                        f"Starting workflow {workflow_name!r} (index {idx_wf}): fatal catalog error — "
                        f"PartialEdge at index {idx_e} target label {lab!r} has no new node id."
                    )
                edge.target = NodeId(new)
        elif isinstance(edge, Edge):
            for end in ("source", "target"):
                node_id_obj = getattr(edge, end)
                old = node_id_obj.root
                lab = old_id_to_label.get(old)
                if lab is None:
                    raise ValueError(
                        f"Starting workflow {workflow_name!r} (index {idx_wf}): fatal catalog error — "
                        f"edge {edge.id!r} endpoint {end!r} references unknown node id {old!r}."
                    )
                new = label_to_new_id.get(lab)
                if new is None:
                    raise ValueError(
                        f"Starting workflow {workflow_name!r} (index {idx_wf}): fatal catalog error — "
                        f"edge {edge.id!r} endpoint {end!r} label {lab!r} has no new node id."
                    )
                setattr(edge, end, NodeId(new))


def set_starting_workflows() -> None:
    """
    Set the starting workflows from the starting_workflows.json file.
    This function should only be called once at startup.
    """
    global _INITIALIZED
    global _STARTING_WORKFLOWS

    if _INITIALIZED:
        return
    with _INIT_LOCK:
        _STARTING_WORKFLOWS = _load_and_validate_starting_workflows_from_file(_STARTING_WORKFLOWS_FILE)
        _INITIALIZED = True


def _load_and_validate_starting_workflows_from_file(target: Path) -> dict[str, Workflow]:
    """Load a starting-workflows JSON file and validate each entry.

    Parameters
    ----------
    target:
        Filesystem path to the JSON data file.

    Returns
    -------
    dict[str, Workflow]
        Mapping of workflow name to validated Workflow model.  Entries that
        fail Pydantic validation are logged and skipped so the server can
        still start with the remaining valid workflows.
    """
    if target is None or not str(target).strip():
        raise ValueError("target path must not be empty")

    if not target.is_file():
        raise FileNotFoundError(f"Starting workflows data file not found: {target}")

    try:
        with open(target, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        logger.error("Failed to decode %s: %s", target, exc)
        return {}

    if not isinstance(data, list):
        logger.error("Expected a JSON array in %s, got %s", target, type(data).__name__)
        return {}

    validated_workflows: dict[str, Workflow] = {}
    for idx_wf, entry in enumerate(data):
        try:
            validated_entry_initial = Workflow.model_validate(entry)

            old_id_to_label = _require_old_id_to_unique_label(
                validated_entry_initial.starting_topology.nodes,
                workflow_name=validated_entry_initial.name,
                idx_wf=idx_wf,
            )
            label_to_new_id: dict[str, str] = {}

            # Only agent nodes carry an agent_record_uri; attempt to load and validate the record,
            # and derive a stable agent id (uuid5) from the record's ``name`` field.
            for idx_nd, node in enumerate[TopologyNodeItem](validated_entry_initial.starting_topology.nodes):
                if isinstance(node, (AgentNode, PartialAgentNode)):
                    # If the agent record cannot be loaded or is invalid we keep the workflow but leave stable_agent_id unset;
                    # in the future these should become grounds for invalidating the workflow entirely.
                    try:
                        record = _load_agent_record_from_uri(node.agent_record_uri, base_path=target.parent)
                        stable_uuid = stable_agent_uuid_for_name(record["name"])
                        node.stable_agent_id = stable_agent_id_from_uuid(stable_uuid)
                        register_from_record(str(stable_uuid), record)
                    # FileNotFoundError is a subclass of OSError.
                    except (FileNotFoundError, httpx.RequestError) as exc:
                        logger.warning("Failed to load agent record for node at index %d (id %s) in workflow at index %d (name %s) but will use the workflow anyhow: %s",
                                       idx_nd, node.id, idx_wf, validated_entry_initial.name, exc)
                    except ValueError as exc:
                        logger.warning("Agent record validation failed for node at index %d (id %s) in workflow at index %d (name %s) but will use the workflow anyhow: %s",
                                       idx_nd, node.id, idx_wf, validated_entry_initial.name, exc)

                # Set the runtime/instance node id. This is not the same as the stable agent id.
                old_node_id = node.id.root
                node.id = node_id_from_uuid(uuid4())
                new_node_id = node.id.root
                label_to_new_id[old_id_to_label[old_node_id]] = new_node_id

            _remap_starting_topology_edge_endpoints(
                validated_entry_initial.starting_topology.edges,
                old_id_to_label,
                label_to_new_id,
                workflow_name=validated_entry_initial.name,
                idx_wf=idx_wf,
            )

            for edge in validated_entry_initial.starting_topology.edges:
                edge.id = edge_id_from_uuid(uuid4())
            
            # Validate the workflow again to ensure that modifications made are valid.
            # Note that model_validate() returns a new instance of the model.
            validated_workflow = Workflow.model_validate(validated_entry_initial.model_dump())

            if validated_workflow.name in validated_workflows:
                logger.warning("Duplicate workflow name %r at index %d; overwriting previous entry", validated_workflow.name, idx_wf)

            validated_workflows[validated_workflow.name] = validated_workflow

        except ValidationError as exc:
            name = entry.get("name", "<unknown>") if isinstance(entry, dict) else "<unknown>"
            logger.warning("Skipping workflow at index %d (%s): validation failed:\n%s", idx_wf, name, exc)

    logger.info("Loaded %d of %d workflow(s) from %s", len(validated_workflows), len(data), target)
    return validated_workflows


def _load_agent_record_from_uri(uri: str, base_path: Path | None = None) -> dict:
    """Load an agent record from a local or remote JSON file.

    Parameters
    ----------
    uri:
        Local filesystem path or remote URL pointing to a JSON file.
        Must contain a root ``name`` field.
    base_path:
        Optional root directory for resolving relative local paths.

    Returns
    -------
    dict
        The parsed agent record.
    """
    if uri.startswith(("http://", "https://")):
        response = httpx.get(uri, follow_redirects=False, timeout=20.0)
        response.raise_for_status()
        data = response.json()
    else:
        resolved = (base_path / uri) if base_path else Path(uri)
        resolved = resolved.resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Agent record file not found: {resolved}")
        with open(resolved, encoding="utf-8") as fh:
            data = json.load(fh)

    if not isinstance(data, dict) or not data.get("name"):
        raise ValueError(f"Agent record JSON at {uri!r} must be an object with a 'name' field")

    return data


def get_workflows() -> dict[str, Workflow]:
    """
    The current implementation of this function where it only returns a dict of workflows from memory is temporary.
    After the store is implemented, this function will likely have to return workflows from the store.
    """
    return _STARTING_WORKFLOWS
