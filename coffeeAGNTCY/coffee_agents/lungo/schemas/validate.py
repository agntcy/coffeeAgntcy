# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Validate a payload against the session state progress JSON schema. Used by A2A middleware (#452) and tests."""

from pathlib import Path

_SCHEMA_PATH = Path(__file__).resolve().parent / "session_state_progress_v1.json"


def get_schema():
    """Load and return the session state progress schema as a dict."""
    import json

    with open(_SCHEMA_PATH, encoding="utf-8") as f:
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

    schema = get_schema()
    jsonschema.validate(instance=payload, schema=schema)
