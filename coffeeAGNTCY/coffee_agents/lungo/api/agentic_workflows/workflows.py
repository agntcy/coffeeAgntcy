# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Load and validate the catalog of starting workflows.

Validates ``starting_workflows.json`` against the ``starting_workflows_v1`` JSON Schema 
(which transitively references ``event_v1``) and exposes the validated workflow definitions
for use by other modules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

from schema import errors, validation

_DATA_DIR = Path(__file__).resolve().parent
_STARTING_WORKFLOWS_FILE = _DATA_DIR / "starting_workflows.json"
_SCHEMA_NAME = "starting_workflows_v1"

# starting_workflows_v1 → $ref event_v1 → $ref event_type_v1
_REF_SCHEMAS = ("event_v1", "event_type_v1")


def _build_validation_registry() -> Registry:
    """Build a ``referencing.Registry`` with every schema reachable via ``$ref``."""
    pairs: list[tuple[str, Resource]] = []
    for name in _REF_SCHEMAS:
        doc = validation.get_schema(name)
        rid = doc.get("$id")
        if rid:
            pairs.append((rid, Resource.from_contents(doc)))
    return Registry().with_resources(pairs)


def _load_and_validate_starting_workflows_from_file(
    target: Path = _STARTING_WORKFLOWS_FILE,
) -> list[dict[str, Any]]:
    """Load a starting-workflows JSON file and validate it.

    Parameters
    ----------
    path:
        Filesystem path to the JSON data file.  Defaults to
        ``starting_workflows.json`` co-located with this module.

    Returns
    -------
    list[dict[str, Any]]
        Validated list of workflow definition dicts.

    Raises
    ------
    FileNotFoundError
        Data file does not exist.
    schema.errors.InstanceDecodeError
        File is not valid JSON.
    schema.errors.SchemaValidationError
        Data does not conform to ``starting_workflows_v1``.
    schema.errors.SchemaNotFoundError
        A required schema definition could not be located.
    schema.errors.SchemaDefinitionError
        A schema definition itself is malformed.
    """
    if not target.is_file():
        raise FileNotFoundError(
            f"Starting workflows data file not found: {target}"
        )

    try:
        with open(target, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise errors.InstanceDecodeError(str(exc)) from exc

    schema_doc = validation.get_schema(_SCHEMA_NAME)
    registry = _build_validation_registry()

    try:
        jsonschema.validate(
            instance=data,
            schema=schema_doc,
            cls=jsonschema.Draft202012Validator,
            registry=registry,
        )
    except jsonschema.ValidationError as exc:
        raise errors.SchemaValidationError(exc.message) from exc
    except Unresolvable as exc:
        raise errors.SchemaValidationError(
            str(exc.__cause__ or exc)
        ) from exc

    return data


_cached_workflows: list[dict[str, Any]] | None = None


def get_starting_workflows() -> list[dict[str, Any]]:
    """Return the validated starting workflows, loading on first access.

    The result is cached process-wide after the first successful load.
    Callers **must not** mutate the returned structure.
    """
    global _cached_workflows
    if _cached_workflows is None:
        _cached_workflows = _load_and_validate_starting_workflows_from_file()
    return _cached_workflows


def clear_cached_workflows() -> None:
    """Discard the cached workflows (useful in tests or after file edits)."""
    global _cached_workflows
    _cached_workflows = None
