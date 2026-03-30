# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Schemas and validation for Lungo.

Schema definitions
--------------------
Schema files live under their respective schema folders, based on their type, like ``schema/jsonschemas/`` for json schemas.
Each file includes the version in the name for stable reference.

Business event types are defined in separate registry file, that can be updated independently of the schemas.
Emitters can add their own event types to the registry, but they must be registered before they can be used in a session.


Examples
--------------------
Example files appear under the schema folders, for example ``schema/jsonschemas/examples/``.
These files can be used as a reference for developers to understand the schema and for tests.
Naming convention is ``{schema_stem}_{example_purpose}.json``, e.g.: ``session_state_progress_v1_snapshot.json``.


Validation
----------
The package exposes ``schema.validation`` and corresponding ``schema.errors`` 
for various validation purposes.
The main purpose of the validation is to validate the structure of 
a data package (payload instance) against a specific schema, 
but it also exposes functions to validate schema definitions, 
that are useful when creating new schemas or new versions of existing schemas.

Example for validating a session state progress payload against the v1 schema:

Python::
    from schema.validation import validate_data_against_schema
    validate_data_against_schema(payload, "session_state_progress_v1")
or:
    from pathlib import Path
    from schema.validation import validate_datafile_against_schema
    validate_datafile_against_schema(Path("path/to/payload.json"), "session_state_progress_v1")

CLI::
    python -m schema.validate instance-string session_state_progress_v1 '{"session_id":"s1",...}'
or:
    python -m schema.validate instances session_state_progress_v1 path/to/payload.json

Versioning
----------
Schemas are versioned in the file name. New versions are added as separate files (e.g.
``session_state_progress_v2.json``) without replacing prior versions.
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
    validate_data_string_against_schema,
    validate_datafile_against_schema,
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
    "validate_datafile_against_schema",
    "validate_data_string_against_schema",
]
