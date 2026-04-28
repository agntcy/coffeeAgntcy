# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Package-specific schema errors.

Callers (including ``schema.validate`` and application code) should catch these
types—not ``jsonschema`` or raw ``json`` exceptions. Third-party errors are
chained via ``raise ... from`` where applicable.
"""

from __future__ import annotations

from pathlib import Path


class SchemaError(Exception):
    """Base class for failures in the ``schema`` package."""


class SchemaNotFoundError(SchemaError):
    """No packaged definition matches the given logical name."""


class AmbiguousSchemaNameError(SchemaError):
    """More than one packaged definition file matches the given stem."""


class SchemaDefinitionError(SchemaError):
    """A definition document is missing, unreadable, or fails meta-validation."""

    def __init__(self, message: str, path: Path | None = None):
        super().__init__(message)
        self.path = path


class SchemaValidationError(SchemaError):
    """Instance data does not satisfy the definition."""


class InstanceDecodeError(SchemaError):
    """Instance payload could not be decoded (e.g. invalid JSON in a file)."""
