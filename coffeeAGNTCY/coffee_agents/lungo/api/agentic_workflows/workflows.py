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

from schema.types import EdgeId, NodeId, TopologyNodeItem, Workflow


logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent
_STARTING_WORKFLOWS_FILE = _DATA_DIR / "starting_workflows.json"

_STARTING_WORKFLOWS: list[Workflow] | None = None

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


def _load_and_validate_starting_workflows_from_file(target: Path) -> list[Workflow]:
    """Load a starting-workflows JSON file and validate each entry.

    Parameters
    ----------
    target:
        Filesystem path to the JSON data file.

    Returns
    -------
    list[Workflow]
        Validated Workflow models.  Entries that fail Pydantic validation
        are logged and skipped so the server can still start with the remaining valid workflows.
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
        return []

    if not isinstance(data, list):
        logger.error("Expected a JSON array in %s, got %s", target, type(data).__name__)
        return []

    validated_workflows: list[Workflow] = []
    for idx_wf, entry in enumerate(data):
        try:
            validated_entry_initial = Workflow.model_validate(entry)

            # If entry has a agent_record_uri field, attempt to load the agent record and validate it.
            for idx_nd, node in enumerate[TopologyNodeItem](validated_entry_initial.starting_topology.nodes):
                # Note: not all workflow nodes are agents.
                if node.agent_record_uri:
                    # Currently, we are checking that the agent record is accessible and valid (for the puposes of id generation),
                    # but we are not doing anything with the agent record itself so we are not invalidating the workflow on these grounds.
                    # In the future, these should be grounds for invalidating the workflow.
                    try:
                        _load_agent_record_from_uri(node.agent_record_uri, base_path=target.parent)
                    # FileNotFoundError is a subclass of OSError.
                    except (FileNotFoundError, httpx.HTTPStatusError) as exc:
                        logger.warning("Failed to load agent record for node at index %d (id %s) in workflow at index %d (name %s) but will use the workflow anyhow: %s",
                                       idx_nd, node.id, idx_wf, validated_entry_initial.name, exc)
                    except ValueError as exc:
                        logger.warning("Agent record validation failed for node at index %d (id %s) in workflow at index %d (name %s) but will use the workflow anyhow: %s",
                                       idx_nd, node.id, idx_wf, validated_entry_initial.name, exc)
                
                node.id = NodeId(f"node://{uuid4()}")
            
            for edge in validated_entry_initial.starting_topology.edges:
                edge.id = EdgeId(f"edge://{uuid4()}")
            
            # Validate the workflow again to ensure that modifications made are valid.
            # Note that model_validate() returns a new instance of the model.
            validated_workflows.append(Workflow.model_validate(validated_entry_initial.model_dump()))

        except ValidationError as exc:
            name = entry.get("name", "<unknown>") if isinstance(entry, dict) else "<unknown>"
            logger.warning("Skipping workflow at index %d (%s): validation failed:\n%s", idx_wf, name, exc)

    logger.info("Loaded %d of %d workflow(s) from %s", len(validated_workflows), len(data), target)
    print(f"Loaded {len(validated_workflows)} of {len(data)} workflow(s) from {target}")
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

    # The 'name' field would be the one used to generate a UUIDv5 node id from the agent record.
    # We are not doing that yet, but we are considering that as a "stable agent id" that would be used to identify the agent across runs.
    # This stable id would be a different field from the runtime/instance id that is currently under the node.id field.
    if not isinstance(data, dict) or not data.get("name"):
        raise ValueError(f"Agent record JSON at {uri!r} must be an object with a 'name' field")

    return data


def get_workflows() -> list[Workflow]:
    """
    The current implementation of this function where it only returns a list of workflows from memory is temporary.
    After the store is implemented, this function will likely have to return a list of workflows from the store.
    """
    return _STARTING_WORKFLOWS
