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
from uuid import NAMESPACE_DNS, uuid4, uuid5

import httpx
from pydantic import ValidationError

from schema.types import (
    AgentId,
    AgentNode,
    AgentPartialNode,
    EdgeId,
    NodeId,
    TopologyNodeItem,
    Workflow,
)


logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent
_STARTING_WORKFLOWS_FILE = _DATA_DIR / "starting_workflows.json"

# Namespace used to derive deterministic stable agent ids (uuid5) from agent record
# names. Built once at import time as uuid5(NAMESPACE_DNS, <dns-like label>) so that
# the same agent name always maps to the same stable id across runs and processes.
_STABLE_AGENT_ID_NAMESPACE = uuid5(NAMESPACE_DNS, "agent.workflow.lungo.coffeeAGNTCY.com")

# Mapping of workflow name to validated Workflow model.
_STARTING_WORKFLOWS: dict[str, Workflow] | None = None

# This is a global lock to ensure that the starting workflows are initialized only once.
_INIT_LOCK = Lock()
_INITIALIZED = False


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

            # Only agent nodes carry an agent_record_uri; attempt to load and validate the record,
            # and derive a stable agent id (uuid5) from the record's ``name`` field.
            for idx_nd, node in enumerate[TopologyNodeItem](validated_entry_initial.starting_topology.nodes):
                if isinstance(node, (AgentNode, AgentPartialNode)):
                    # If the agent record cannot be loaded or is invalid we keep the workflow but leave stable_agent_id unset;
                    # in the future these should become grounds for invalidating the workflow entirely.
                    try:
                        record = _load_agent_record_from_uri(node.agent_record_uri, base_path=target.parent)
                        stable_agent_uuid = uuid5(_STABLE_AGENT_ID_NAMESPACE, record["name"])
                        node.stable_agent_id = AgentId(f"agent://{stable_agent_uuid}")
                    # FileNotFoundError is a subclass of OSError.
                    except (FileNotFoundError, httpx.HTTPStatusError) as exc:
                        logger.warning("Failed to load agent record for node at index %d (id %s) in workflow at index %d (name %s) but will use the workflow anyhow: %s",
                                       idx_nd, node.id, idx_wf, validated_entry_initial.name, exc)
                    except ValueError as exc:
                        logger.warning("Agent record validation failed for node at index %d (id %s) in workflow at index %d (name %s) but will use the workflow anyhow: %s",
                                       idx_nd, node.id, idx_wf, validated_entry_initial.name, exc)

                # Set the runtime/instance node id. This is not the same as the stable agent id.
                node.id = NodeId(f"node://{uuid4()}")
            
            for edge in validated_entry_initial.starting_topology.edges:
                edge.id = EdgeId(f"edge://{uuid4()}")
            
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
        response = httpx.get(uri, follow_redirects=False)
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
