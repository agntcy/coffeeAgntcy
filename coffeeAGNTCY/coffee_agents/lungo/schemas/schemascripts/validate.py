# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Validate payloads against JSON schemas. Used by A2A middleware (#452) and tests."""

import json
from pathlib import Path

_SCHEMAFILES_DIR = Path(__file__).resolve().parent.parent / "schemafiles"
EXAMPLES_DIR = _SCHEMAFILES_DIR.parent / "examples"


def _schema_paths():
    """Yield paths to all JSON schema files in schemafiles."""
    if not _SCHEMAFILES_DIR.exists():
        return
    for p in sorted(_SCHEMAFILES_DIR.glob("*.json")):
        yield p


def get_schema(schema_name: str) -> dict:
    """Load and return a schema as a dict."""
    candidates = list(_SCHEMAFILES_DIR.glob(f"{schema_name}*.json"))
    if not candidates:
        raise FileNotFoundError(f"No schema matching {schema_name!r} in {_SCHEMAFILES_DIR}")
    with open(candidates[0], encoding="utf-8") as f:
        return json.load(f)


def validate_session_state_progress(payload: dict) -> None:
    """
    Validate payload against the session state progress schema.
    Raises jsonschema.ValidationError if invalid.
    Requires: pip install jsonschema
    """
    try:
        import jsonschema
    except ImportError as e:
        raise ImportError(
            "Session state progress validation requires jsonschema. Install with: pip install jsonschema"
        ) from e

    schema = get_schema("session_state_progress_v1")
    jsonschema.validate(instance=payload, schema=schema)


def validate_all_schemas() -> list[tuple[Path, str | None]]:
    """
    Scan schemafiles/ and validate each JSON file is a valid JSON schema.
    Returns list of (path, error_message) for failures; empty list if all pass.
    """
    try:
        import jsonschema
    except ImportError as e:
        raise ImportError(
            "Schema validation requires jsonschema. Install with: pip install jsonschema"
        ) from e

    failures: list[tuple[Path, str | None]] = []
    for path in _schema_paths():
        try:
            with open(path, encoding="utf-8") as f:
                schema = json.load(f)
        except json.JSONDecodeError as e:
            failures.append((path, f"Invalid JSON: {e}"))
            continue
        try:
            jsonschema.Draft202012Validator.check_schema(schema)
        except jsonschema.SchemaError as e:
            failures.append((path, str(e)))
    return failures


if __name__ == "__main__":
    import sys

    failures = validate_all_schemas()
    if failures:
        for path, err in failures:
            print(f"{path}: {err}", file=sys.stderr)
        sys.exit(1)
    print("All schemas valid.")
