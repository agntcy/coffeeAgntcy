# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for session state progress schema and validator."""

import json
from pathlib import Path

import jsonschema
import pytest

import schemas.validate as _validate_module
from schemas.validate import get_schema, validate_session_state_progress


def test_get_schema_returns_dict_with_required_structure():
    schema = get_schema()
    assert isinstance(schema, dict)
    assert "$id" in schema
    assert "session_state_progress_v1.json" in schema["$id"]
    assert schema.get("type") == "object"
    required = schema.get("required", [])
    assert "session_id" in required
    assert "kind" in required
    assert "timestamp" in required
    assert "properties" in schema
    assert "$defs" in schema


def test_validate_valid_snapshot_minimal():
    payload = {
        "session_id": "s1",
        "kind": "snapshot",
        "timestamp": "2026-01-01T00:00:00Z",
        "state": {},
    }
    validate_session_state_progress(payload)


def test_validate_valid_delta_minimal():
    payload = {
        "session_id": "s1",
        "kind": "delta",
        "timestamp": "2026-01-01T00:00:00Z",
        "event_type": "node_entered",
    }
    validate_session_state_progress(payload)


def test_validate_example_files():
    examples_dir = Path(_validate_module.__file__).resolve().parent / "examples"
    for name in ("snapshot_example.json", "delta_example.json"):
        with open(examples_dir / name, encoding="utf-8") as f:
            payload = json.load(f)
        validate_session_state_progress(payload)


def test_validate_invalid_missing_required_field():
    payload = {
        "kind": "snapshot",
        "timestamp": "2026-01-01T00:00:00Z",
        "state": {},
    }
    with pytest.raises(jsonschema.ValidationError):
        validate_session_state_progress(payload)


def test_validate_invalid_snapshot_without_state():
    payload = {
        "session_id": "s1",
        "kind": "snapshot",
        "timestamp": "2026-01-01T00:00:00Z",
    }
    with pytest.raises(jsonschema.ValidationError):
        validate_session_state_progress(payload)


def test_validate_invalid_delta_without_event_type():
    payload = {
        "session_id": "s1",
        "kind": "delta",
        "timestamp": "2026-01-01T00:00:00Z",
    }
    with pytest.raises(jsonschema.ValidationError):
        validate_session_state_progress(payload)

