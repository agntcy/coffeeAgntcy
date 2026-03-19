# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for session state progress schema and validator."""

import json
from pathlib import Path

import jsonschema
import pytest

from schemas.schemascripts.validate import (
    EXAMPLES_DIR,
    get_schema,
    validate_all_schemas,
    validate_session_state_progress,
)


def test_get_schema_returns_dict_with_required_structure():
    schema = get_schema("session_state_progress_v1")
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


@pytest.mark.parametrize("payload", [
    {"session_id": "s1", "kind": "snapshot", "timestamp": "2026-01-01T00:00:00Z", "state": {}},
    {"session_id": "s1", "kind": "event", "timestamp": "2026-01-01T00:00:00Z", "event_type": "node_entered"},
], ids=["snapshot_minimal", "event_minimal"])
def test_validate_valid_payloads(payload):
    validate_session_state_progress(payload)


@pytest.mark.parametrize("example_file", ["snapshot_example.json", "event_example.json"])
def test_validate_example_files(example_file):
    with open(EXAMPLES_DIR / example_file, encoding="utf-8") as f:
        payload = json.load(f)
    validate_session_state_progress(payload)


@pytest.mark.parametrize("payload", [
    {"kind": "snapshot", "timestamp": "2026-01-01T00:00:00Z", "state": {}},
    {"session_id": "s1", "kind": "snapshot", "timestamp": "2026-01-01T00:00:00Z"},
    {"session_id": "s1", "kind": "event", "timestamp": "2026-01-01T00:00:00Z"},
], ids=["missing_required_field", "snapshot_without_state", "event_without_event_type"])
def test_validate_invalid_payloads_raise(payload):
    with pytest.raises(jsonschema.ValidationError):
        validate_session_state_progress(payload)


@pytest.mark.parametrize("schema_name,expect_error,match", [
    ("session_state_progress_v1", False, "session_state_progress_v1.json"),
    ("nonexistent", True, "No schema matching"),
], ids=["found", "not_found"])
def test_get_schema(schema_name, expect_error, match):
    if expect_error:
        with pytest.raises(FileNotFoundError, match=match):
            get_schema(schema_name)
    else:
        schema = get_schema(schema_name)
        assert schema.get("$id", "").endswith(match)


def test_validate_all_schemas_passes():
    failures = validate_all_schemas()
    assert failures == []


def _run_validate_all_schemas_with_dir(tmp_path):
    from schemas.schemascripts import validate as mod

    orig_dir = mod._SCHEMAFILES_DIR
    try:
        mod._SCHEMAFILES_DIR = tmp_path
        return mod.validate_all_schemas()
    finally:
        mod._SCHEMAFILES_DIR = orig_dir


@pytest.mark.parametrize("filename,content,expected_in_error", [
    ("invalid.json", '{"type": "invalid_type"}', "invalid_type"),
    ("bad.json", "{ invalid json }", "Invalid JSON"),
], ids=["invalid_schema", "invalid_json"])
def test_validate_all_schemas_detects_failures(tmp_path, filename, content, expected_in_error):
    (tmp_path / filename).write_text(content)
    failures = _run_validate_all_schemas_with_dir(tmp_path)
    assert len(failures) == 1
    assert failures[0][0].name == filename
    assert expected_in_error in (failures[0][1] or "")


def test_validate_all_schemas_empty_dir_returns_empty(tmp_path):
    failures = _run_validate_all_schemas_with_dir(tmp_path)
    assert failures == []


def test_validate_all_schemas_multiple_failures(tmp_path):
    (tmp_path / "a.json").write_text('{"type": "nope"}')
    (tmp_path / "b.json").write_text("not json at all")
    failures = _run_validate_all_schemas_with_dir(tmp_path)
    assert len(failures) == 2
    paths = {f[0].name for f in failures}
    assert paths == {"a.json", "b.json"}

