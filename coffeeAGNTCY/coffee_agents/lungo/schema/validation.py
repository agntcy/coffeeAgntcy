# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Schema-agnostic validation: dispatch to registered definition backends."""

from pathlib import Path

from schema import errors
from schema.definition_backend import DefinitionBackend
from schema.json_schema import packaged_json_schema_backend

_BACKENDS: tuple[DefinitionBackend, ...] = (packaged_json_schema_backend,)


def _backend_for_schema(schema_name: str) -> DefinitionBackend:
    for backend in _BACKENDS:
        if backend.owns_schema(schema_name):
            return backend
    raise errors.SchemaNotFoundError(f"Unknown schema {schema_name!r}")


def validate_definition(schema_name: str) -> Path:
    """Meta-validate one packaged definition. Raises SchemaNotFoundError if unknown."""
    return _backend_for_schema(schema_name).validate_definition(schema_name)


def validate_all_definitions() -> list[errors.SchemaDefinitionError]:
    """Meta-validate all definitions from all backends."""
    failures: list[errors.SchemaDefinitionError] = []
    for backend in _BACKENDS:
        failures.extend(backend.validate_all_definitions())
    return failures


def validate_data_against_schema(data: dict, schema_name: str) -> None:
    """Validate ``data`` against the named schema. Raises SchemaNotFoundError if unknown."""
    _backend_for_schema(schema_name).validate_data(data, schema_name)


def validate_file_against_schema(path: Path, schema_name: str) -> None:
    """Parse instance file with the backend for ``schema_name``, then validate. Raises domain errors from parse or validate."""
    backend = _backend_for_schema(schema_name)
    data = backend.parse_instance_file(path)
    backend.validate_data(data, schema_name)


def validate_string_against_schema(text: str, schema_name: str) -> None:
    """Parse instance text with the backend for ``schema_name``, then validate."""
    backend = _backend_for_schema(schema_name)
    data = backend.parse_instance_text(text)
    backend.validate_data(data, schema_name)


def get_schema(schema_name: str) -> dict:
    """Return the packaged schema definition as a dict.
       Raises SchemaNotFoundError if unknown; backend-specific errors (e.g. SchemaDefinitionError, AmbiguousSchemaNameError) may apply."""
    return _backend_for_schema(schema_name).get_schema(schema_name)
