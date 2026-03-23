# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for session state progress schema and validator."""

import json
from dataclasses import dataclass
from typing import Any

import jsonschema
import pytest

from schemas.schemascripts.validate import (
    EXAMPLES_DIR,
    get_schema,
    validate_all_schemas,
    validate_session_state_progress,
)


@dataclass
class SessionStateProgressPayloadCase:
    """Payload under test for session_state_progress validation."""

    payload: dict[str, Any]


@dataclass
class GetSchemaCase:
    """get_schema lookup: expect a dict or FileNotFoundError."""

    schema_name: str
    expect_error: bool
    match: str


@dataclass
class BadSchemaFileCase:
    """Temp schema file expected to fail validate_all_schemas."""

    filename: str
    content: str
    expected_in_error: str


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


_VALID_PAYLOAD_CASES = [
    pytest.param(
        SessionStateProgressPayloadCase(
            payload={
                "session_id": "s1",
                "kind": "snapshot",
                "timestamp": "2026-01-01T00:00:00Z",
                "state": {},
            },
        ),
        id="minimal_snapshot_valid",
    ),
    pytest.param(
        SessionStateProgressPayloadCase(
            payload={
                "session_id": "s1",
                "kind": "event",
                "timestamp": "2026-01-01T00:00:00Z",
                "event_type": "node_entered",
            },
        ),
        id="minimal_event_valid",
    ),
]


@pytest.mark.parametrize("case", _VALID_PAYLOAD_CASES)
def test_validate_valid_payloads(case: SessionStateProgressPayloadCase):
    validate_session_state_progress(case.payload)


@pytest.mark.parametrize(
    "example_file",
    [
        pytest.param("snapshot_example.json", id="valid_snapshot_example_file"),
        pytest.param("event_example.json", id="valid_event_example_file"),
    ],
)
def test_validate_example_files(example_file):
    with open(EXAMPLES_DIR / example_file, encoding="utf-8") as f:
        payload = json.load(f)
    validate_session_state_progress(payload)


_INVALID_PAYLOAD_CASES = [
    pytest.param(
        SessionStateProgressPayloadCase(
            payload={
                "kind": "snapshot",
                "timestamp": "2026-01-01T00:00:00Z",
                "state": {},
            },
        ),
        id="rejects_missing_session_id",
    ),
    pytest.param(
        SessionStateProgressPayloadCase(
            payload={
                "session_id": "s1",
                "kind": "snapshot",
                "timestamp": "2026-01-01T00:00:00Z",
            },
        ),
        id="rejects_snapshot_without_state",
    ),
    pytest.param(
        SessionStateProgressPayloadCase(
            payload={
                "session_id": "s1",
                "kind": "event",
                "timestamp": "2026-01-01T00:00:00Z",
            },
        ),
        id="rejects_event_without_event_type",
    ),
]


@pytest.mark.parametrize("case", _INVALID_PAYLOAD_CASES)
def test_validate_invalid_payloads_raise(case: SessionStateProgressPayloadCase):
    with pytest.raises(jsonschema.ValidationError):
        validate_session_state_progress(case.payload)


_GET_SCHEMA_CASES = [
    pytest.param(
        GetSchemaCase(
            schema_name="session_state_progress_v1",
            expect_error=False,
            match="session_state_progress_v1.json",
        ),
        id="schema_found",
    ),
    pytest.param(
        GetSchemaCase(
            schema_name="nonexistent",
            expect_error=True,
            match="No schema matching",
        ),
        id="schema_not_found",
    ),
]


@pytest.mark.parametrize("case", _GET_SCHEMA_CASES)
def test_get_schema(case: GetSchemaCase):
    if case.expect_error:
        with pytest.raises(FileNotFoundError, match=case.match):
            get_schema(case.schema_name)
    else:
        schema = get_schema(case.schema_name)
        assert schema.get("$id", "").endswith(case.match)


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


_BAD_SCHEMA_FILE_CASES = [
    pytest.param(
        BadSchemaFileCase(
            filename="invalid.json",
            content='{"type": "invalid_type"}',
            expected_in_error="invalid_type",
        ),
        id="invalid_json_schema_type",
    ),
    pytest.param(
        BadSchemaFileCase(
            filename="bad.json",
            content="{ invalid json }",
            expected_in_error="Invalid JSON",
        ),
        id="malformed_json_file",
    ),
]


@pytest.mark.parametrize("case", _BAD_SCHEMA_FILE_CASES)
def test_validate_all_schemas_detects_failures(tmp_path, case: BadSchemaFileCase):
    (tmp_path / case.filename).write_text(case.content)
    failures = _run_validate_all_schemas_with_dir(tmp_path)
    assert len(failures) == 1
    assert failures[0][0].name == case.filename
    assert case.expected_in_error in (failures[0][1] or "")


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
