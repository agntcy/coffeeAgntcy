# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""
JSON Schema file loading and validation functions. 
Maps library errors to ``schema.errors``.

This module is the JSON specific implementation of the validation layer.
It also implements its own version of ``DefinitionBackend`` interface for JSON Schemas.

DO NOT import this module directly, use ``schema.validation`` instead, 
which imports and wraps it properly.
(Unless imported for unit tests or integration tests specifically targeting JSON mechanics.)
"""

import json
from pathlib import Path

import jsonschema
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable

from schema import errors
from schema.definition_backend import DefinitionBackend

_JSONSCHEMA_SPECS_DIR = Path(__file__).resolve().parent / "jsonschemas"

_EVENT_TYPE_V1_FILE = "event_type_v1.json"

# Process-local cache; invalidated when event_type_v1.json mtime changes.
_event_type_v1_doc_cache: tuple[Path, float, dict] | None = None


def clear_event_type_v1_cache() -> None:
    """Clear the cached event type list schema document (for tests or after on-disk edits)."""
    global _event_type_v1_doc_cache
    _event_type_v1_doc_cache = None


def _parse_event_types(path: Path) -> dict:
    """Read and validate ``event_type_v1.json`` shape; raise SchemaDefinitionError on failure."""
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        raise errors.SchemaDefinitionError(f"Invalid JSON: {e}", path=path) from e
    if not isinstance(raw, dict):
        raise errors.SchemaDefinitionError(
            "event_type_v1.json must be a JSON Schema object", path=path
        )
    rid = raw.get("$id")
    if not isinstance(rid, str) or not rid.strip():
        raise errors.SchemaDefinitionError(
            "event_type_v1.json must have a non-empty string $id", path=path
        )
    defs = raw.get("$defs")
    if not isinstance(defs, dict):
        raise errors.SchemaDefinitionError(
            "event_type_v1.json missing $defs", path=path
        )
    event_type = defs.get("event_type")
    if not isinstance(event_type, dict):
        raise errors.SchemaDefinitionError(
            "event_type_v1.json missing $defs.event_type", path=path
        )
    enum = event_type.get("enum")
    if not isinstance(enum, list) or not enum:
        raise errors.SchemaDefinitionError(
            "$defs.event_type.enum must be a non-empty array of strings",
            path=path,
        )
    if not all(isinstance(x, str) for x in enum):
        raise errors.SchemaDefinitionError(
            "$defs.event_type.enum must contain only strings", path=path
        )
    return raw


def _get_cached_event_types() -> dict | None:
    """
    Return validated event type list schema dict if the file exists; None if missing.
    Uses path resolve + mtime cache (process-local).
    """
    global _event_type_v1_doc_cache
    path = event_type_v1_path()
    if not path.is_file():
        return None
    resolved = path.resolve()
    mtime = path.stat().st_mtime
    if _event_type_v1_doc_cache is not None:
        c_resolved, c_mtime, c_doc = _event_type_v1_doc_cache
        if c_resolved == resolved and c_mtime == mtime:
            return c_doc
    doc = _parse_event_types(path)
    _event_type_v1_doc_cache = (resolved, mtime, doc)
    return doc


def resolve_json_schema_path(schema_name: str) -> Path:
    """
    Resolve ``schema_name`` to exactly one file under ``jsonschemas/*.json``.
    """
    candidates = sorted(_JSONSCHEMA_SPECS_DIR.glob(f"{schema_name}*.json"))
    if not candidates:
        raise errors.SchemaNotFoundError(
            f"No schema matching {schema_name!r} in {_JSONSCHEMA_SPECS_DIR}"
        )
    if len(candidates) > 1:
        names = [p.name for p in candidates]
        raise errors.AmbiguousSchemaNameError(
            f"Ambiguous schema name {schema_name!r}: matches multiple files {names}"
        )
    return candidates[0]


def get_schema(schema_name: str) -> dict:
    """Load and return a schema dict by stem name (e.g. event_v1)."""
    path = resolve_json_schema_path(schema_name)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise errors.SchemaDefinitionError(f"Invalid JSON in schema file: {e}", path=path) from e


def load_json_instance_file(path: Path) -> dict:
    """Load a JSON object from a user instance file. Raises InstanceDecodeError if parsing fails."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise errors.InstanceDecodeError(str(e)) from e


def parse_json_instance_text(text: str) -> dict:
    """Parse JSON instance from a string. Raises InstanceDecodeError if parsing fails."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise errors.InstanceDecodeError(str(e)) from e


def _schema_paths():
    """Yield paths to JSON schema spec files (top-level jsonschemas/*.json only)."""
    if not _JSONSCHEMA_SPECS_DIR.exists():
        return
    for p in sorted(_JSONSCHEMA_SPECS_DIR.glob("*.json")):
        yield p


def event_type_v1_path() -> Path:
    """Path to ``event_type_v1.json`` (``$defs.event_type`` enum for ``event_v1``)."""
    return _JSONSCHEMA_SPECS_DIR / _EVENT_TYPE_V1_FILE


def _event_type_validation_registry() -> Registry:
    """Referencing registry preloaded with ``event_type_v1.json`` when present on disk."""
    path = event_type_v1_path()
    if not path.is_file():
        return Registry()
    doc = _get_cached_event_types()
    if doc is None:
        raise errors.SchemaDefinitionError(
            f"Event type list schema not found: {path}", path=path
        )
    rid = doc["$id"]
    return Registry().with_resources([(rid, Resource.from_contents(doc))])


def load_event_type_registry() -> list[str]:
    """
    Load known ``metadata.type`` strings from ``$defs.event_type.enum`` in
    ``event_type_v1.json``.
    Raises SchemaDefinitionError if the file is missing or malformed.
    """
    path = event_type_v1_path()
    if not path.is_file():
        raise errors.SchemaDefinitionError(
            f"Event type list schema not found: {path}", path=path
        )
    doc = _get_cached_event_types()
    if doc is None:
        raise errors.SchemaDefinitionError(
            f"Event type list schema not found: {path}", path=path
        )
    enum = doc["$defs"]["event_type"]["enum"]
    return list(enum)


def is_event_type_registered(event_type: str) -> bool:
    """Return True if ``event_type`` is listed in ``event_type_v1.json``."""
    return event_type in load_event_type_registry()


def _validate_json_schema_at_path(path: Path) -> errors.SchemaDefinitionError | None:
    try:
        with open(path, encoding="utf-8") as f:
            schema_doc = json.load(f)
    except json.JSONDecodeError as e:
        err = errors.SchemaDefinitionError(f"Invalid JSON: {e}", path=path)
        err.__cause__ = e
        return err
    try:
        jsonschema.Draft202012Validator.check_schema(schema_doc)
    except jsonschema.SchemaError as e:
        err = errors.SchemaDefinitionError(str(e), path=path)
        err.__cause__ = e
        return err
    return None


def validate_json_schema_definition(schema_name: str) -> Path:
    """Meta-validate one packaged JSON Schema by logical name. Returns path on success."""
    path = resolve_json_schema_path(schema_name)
    err = _validate_json_schema_at_path(path)
    if err is not None:
        raise err
    return path


def validate_all_json_schema_definitions() -> list[errors.SchemaDefinitionError]:
    """
    Meta-validate each file in jsonschemas/*.json.
    Returns a list of errors (empty if all pass).
    """
    failures: list[errors.SchemaDefinitionError] = []
    for path in _schema_paths():
        err = _validate_json_schema_at_path(path)
        if err is not None:
            failures.append(err)
    return failures


def _enforce_workflow_instance_map_key_id_match(instance: dict) -> None:
    """
    Each ``workflow.instances`` map key must equal the nested value's ``id``.
    Not expressible in JSON Schema alone; run after schema validation.
    """
    data = instance.get("data")
    if not isinstance(data, dict):
        return
    workflows = data.get("workflows")
    if not isinstance(workflows, dict):
        return
    for wf_key, wf in workflows.items():
        if not isinstance(wf, dict):
            continue
        instances = wf.get("instances")
        if not isinstance(instances, dict):
            continue
        for map_key, inst in instances.items():
            if not isinstance(inst, dict):
                continue
            iid = inst.get("id")
            if map_key != iid:
                raise errors.SchemaValidationError(
                    f"data.workflows[{wf_key!r}].instances: map key must equal "
                    f"workflow_instance.id (key {map_key!r} != id {iid!r})"
                )


def validate_version_specific_criteria(instance: dict, schema_name: str) -> None:
    """
    Apply validation that depends on the packaged logical schema name (constraints
    that JSON Schema cannot encode in the shared spec).
    """
    if schema_name == "event_v1":
        _enforce_workflow_instance_map_key_id_match(instance)


def validate_json_instance(instance: dict, schema_name: str) -> None:
    """Validate ``instance`` against the named JSON Schema."""
    schema_doc = get_schema(schema_name)
    registry = _event_type_validation_registry()
    try:
        jsonschema.validate(
            instance=instance,
            schema=schema_doc,
            cls=jsonschema.Draft202012Validator,
            registry=registry,
        )
    except jsonschema.ValidationError as e:
        raise errors.SchemaValidationError(e.message) from e
    except Unresolvable as e:
        raise errors.SchemaValidationError(str(e.__cause__ or e)) from e
    validate_version_specific_criteria(instance, schema_name)


class JsonSchemaPackagedBackend:
    """Packaged JSON Schema definitions under ``schema/jsonschemas/``."""

    def owns_schema(self, schema_name: str) -> bool:
        try:
            resolve_json_schema_path(schema_name)
            return True
        except errors.SchemaNotFoundError:
            return False

    def validate_definition(self, schema_name: str) -> Path:
        return validate_json_schema_definition(schema_name)

    def validate_all_definitions(self) -> list[errors.SchemaDefinitionError]:
        return validate_all_json_schema_definitions()

    def validate_data(self, data: dict, schema_name: str) -> None:
        validate_json_instance(data, schema_name)

    def parse_instance_file(self, path: Path) -> dict:
        return load_json_instance_file(path)

    def parse_instance_text(self, text: str) -> dict:
        return parse_json_instance_text(text)

    def get_schema(self, schema_name: str) -> dict:
        return get_schema(schema_name)


packaged_json_schema_backend: DefinitionBackend = JsonSchemaPackagedBackend()
