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

from pydantic import ValidationError

from schema.types import Workflow


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

    validated: list[Workflow] = []
    for idx, entry in enumerate(data):
        try:
            validated.append(Workflow.model_validate(entry))
        except ValidationError as exc:
            name = entry.get("name", "<unknown>") if isinstance(entry, dict) else "<unknown>"
            logger.warning("Skipping workflow at index %d (%s): validation failed:\n%s", idx, name, exc)

    logger.info("Loaded %d of %d workflow(s) from %s", len(validated), len(data), target)
    return validated


def get_workflows() -> list[Workflow]:
    """
    The current implementation of this function where it only returns a list of workflows from memory is temporary.
    After the store is implemented, this function will likely have to return a list of workflows from the store.
    """
    return _STARTING_WORKFLOWS
