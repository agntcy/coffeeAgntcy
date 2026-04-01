# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Schemas and validation for Lungo.

Schema definitions
--------------------
Schema files live under their respective schema folders, based on their type, like ``schema/jsonschemas/`` for json schemas.
Each file includes the version in the name for stable reference.

Business event types are listed in versioned event_type files like ``event_type_v1.json``,
alongside the corresponding schema files, and can be updated independently of the event message shape, so emitters can add their own event types to the list.
The event type list is versioned internally wiht minor versions when additions happen,
and a major version (appearing in the file name) is bumped when something is removed, or other breaking change happens.


Examples
--------------------
Example files appear under the schema folders, for example ``schema/jsonschemas/examples/``.
These files can be used as a reference for developers to understand the schema and for tests.
Naming convention is ``{schema_stem}_{example_purpose}.json``, e.g.: ``event_v1_full.json``.


Validation
----------
The package exposes ``schema.validation`` and corresponding ``schema.errors`` 
for various validation purposes.
The main purpose of the validation is to validate the structure of 
a data package (payload instance) against a specific schema, 
but it also exposes functions to validate schema definitions, 
that are useful when creating new schemas or new versions of existing schemas.

Example for validating an event payload against the v1 schema:

Python::
    from schema.validation import validate_data_against_schema
    validate_data_against_schema(payload, "event_v1")
or:
    from pathlib import Path
    from schema.validation import validate_file_against_schema
    validate_file_against_schema(Path("path/to/payload.json"), "event_v1")

CLI::
    python -m schema.validate instance-string event_v1 '{"metadata":{...},"data":{...}}'
or:
    python -m schema.validate instances event_v1 path/to/payload.json

Versioning
----------
Schemas are versioned in the file name. New versions are added as separate files (e.g.
``event_v2.json``) without replacing prior versions.
"""

from schema.errors import (
    AmbiguousSchemaNameError,
    InstanceDecodeError,
    SchemaDefinitionError,
    SchemaError,
    SchemaNotFoundError,
    SchemaValidationError,
)
from schema.validation import (
    get_schema,
    validate_all_definitions,
    validate_data_against_schema,
    validate_file_against_schema,
    validate_string_against_schema,
    validate_definition,
)

__all__ = [
    "AmbiguousSchemaNameError",
    "InstanceDecodeError",
    "SchemaDefinitionError",
    "SchemaError",
    "SchemaNotFoundError",
    "SchemaValidationError",
    "get_schema",
    "validate_all_definitions",
    "validate_definition",
    "validate_data_against_schema",
    "validate_file_against_schema",
    "validate_string_against_schema",
]
