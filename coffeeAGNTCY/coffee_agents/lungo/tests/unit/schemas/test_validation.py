# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for schema.validation (facade dispatch to backends)."""

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from schema import json_schema as json_schema_mod
from schema import validation as validation_mod
from schema.definition_backend import DefinitionBackend
from schema.errors import AmbiguousSchemaNameError, SchemaDefinitionError, SchemaNotFoundError
from schema.json_schema import get_schema as json_get_schema
from schema.validation import (
    get_schema,
    validate_all_definitions,
    validate_data_against_schema,
    validate_data_string_against_schema,
    validate_datafile_against_schema,
    validate_definition,
)

KNOWN_SCHEMA = "session_state_progress_v1"
_UNKNOWN = "totally_missing_schema_xyz"
_VALID_JSON = (
    '{"session_id": "s1", "kind": "snapshot", "timestamp": "2026-01-01T00:00:00Z", "state": {}}'
)


@pytest.fixture
def json_schema_specs_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setattr(json_schema_mod, "_JSONSCHEMA_SPECS_DIR", tmp_path)
    return tmp_path


def test_portable_get_schema_matches_json_layer_and_structure():
    spec = get_schema(KNOWN_SCHEMA)
    assert isinstance(spec, dict)
    assert "$id" in spec
    assert "session_state_progress_v1.json" in spec["$id"]
    assert spec.get("type") == "object"
    required = spec.get("required", [])
    assert "session_id" in required
    assert "kind" in required
    assert "timestamp" in required
    assert "properties" in spec
    assert "$defs" in spec
    assert spec == json_get_schema(KNOWN_SCHEMA)


def test_validation_get_schema_ambiguous_propagates(json_schema_specs_dir: Path):
    (json_schema_specs_dir / "session_state_progress_v1.json").write_text("{}")
    (json_schema_specs_dir / "session_state_progress_v1_alt.json").write_text("{}")
    with pytest.raises(AmbiguousSchemaNameError, match="Ambiguous"):
        get_schema("session_state_progress_v1")


def _unknown_datafile(specs_dir: Path) -> None:
    ok = specs_dir / "x.json"
    ok.write_text("{}", encoding="utf-8")
    validate_datafile_against_schema(ok, _UNKNOWN)


@pytest.mark.parametrize(
    "invoke",
    [
        pytest.param(lambda _: validate_definition(_UNKNOWN), id="definition"),
        pytest.param(lambda _: validate_data_against_schema({}, _UNKNOWN), id="data_against_schema"),
        pytest.param(lambda _: get_schema(_UNKNOWN), id="get_schema"),
        pytest.param(lambda _: validate_data_string_against_schema(_VALID_JSON, _UNKNOWN), id="data_string"),
        pytest.param(lambda d: _unknown_datafile(d), id="datafile"),
    ],
)
def test_unknown_schema_when_specs_empty(json_schema_specs_dir: Path, invoke: Callable[[Path], None]):
    with pytest.raises(SchemaNotFoundError, match="Unknown schema"):
        invoke(json_schema_specs_dir)


def test_validate_all_definitions_integration_packaged_ok():
    assert validate_all_definitions() == []


def test_validate_all_definitions_concatenates_backends(monkeypatch: pytest.MonkeyPatch):
    e1 = SchemaDefinitionError("one", path=Path("a.json"))
    e2 = SchemaDefinitionError("two", path=Path("b.json"))
    b1 = MagicMock(spec=DefinitionBackend)
    b1.validate_all_definitions.return_value = [e1]
    b2 = MagicMock(spec=DefinitionBackend)
    b2.validate_all_definitions.return_value = [e2]
    monkeypatch.setattr(validation_mod, "_BACKENDS", (b1, b2))
    assert validate_all_definitions() == [e1, e2]
    b1.validate_all_definitions.assert_called_once()
    b2.validate_all_definitions.assert_called_once()


def _backends_with_owner(name: str):
    skip = MagicMock(spec=DefinitionBackend)
    skip.owns_schema = MagicMock(return_value=False)
    pick = MagicMock(spec=DefinitionBackend)
    pick.owns_schema = MagicMock(side_effect=lambda n: n == name)
    pick.validate_data = MagicMock()
    pick.parse_instance_file = MagicMock(return_value={"parsed": "file"})
    pick.parse_instance_text = MagicMock(return_value={"parsed": "text"})
    pick.validate_definition = MagicMock(return_value=Path("/z/schema.json"))
    pick.get_schema = MagicMock(return_value={"doc": True})
    return skip, pick


def test_dispatch_validate_data_against_schema(monkeypatch: pytest.MonkeyPatch):
    skip, pick = _backends_with_owner("x")
    monkeypatch.setattr(validation_mod, "_BACKENDS", (skip, pick))
    validate_data_against_schema({"k": 1}, "x")
    pick.validate_data.assert_called_once_with({"k": 1}, "x")
    skip.validate_data.assert_not_called()


def test_dispatch_validate_datafile(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    skip, pick = _backends_with_owner("x")
    monkeypatch.setattr(validation_mod, "_BACKENDS", (skip, pick))
    p = tmp_path / "inst.json"
    p.write_text("{}", encoding="utf-8")
    validate_datafile_against_schema(p, "x")
    pick.parse_instance_file.assert_called_once_with(p)
    pick.validate_data.assert_called_once_with({"parsed": "file"}, "x")


def test_dispatch_validate_data_string(monkeypatch: pytest.MonkeyPatch):
    skip, pick = _backends_with_owner("x")
    monkeypatch.setattr(validation_mod, "_BACKENDS", (skip, pick))
    validate_data_string_against_schema('{"a":1}', "x")
    pick.parse_instance_text.assert_called_once_with('{"a":1}')
    pick.validate_data.assert_called_once_with({"parsed": "text"}, "x")


def test_dispatch_validate_definition(monkeypatch: pytest.MonkeyPatch):
    skip, pick = _backends_with_owner("x")
    monkeypatch.setattr(validation_mod, "_BACKENDS", (skip, pick))
    out = validate_definition("x")
    assert out == Path("/z/schema.json")
    pick.validate_definition.assert_called_once_with("x")


def test_dispatch_get_schema(monkeypatch: pytest.MonkeyPatch):
    skip, pick = _backends_with_owner("x")
    monkeypatch.setattr(validation_mod, "_BACKENDS", (skip, pick))
    assert get_schema("x") == {"doc": True}
    pick.get_schema.assert_called_once_with("x")


def test_no_backend_owns_raises_unknown_schema(monkeypatch: pytest.MonkeyPatch):
    b1 = MagicMock(spec=DefinitionBackend)
    b1.owns_schema = MagicMock(return_value=False)
    b2 = MagicMock(spec=DefinitionBackend)
    b2.owns_schema = MagicMock(return_value=False)
    monkeypatch.setattr(validation_mod, "_BACKENDS", (b1, b2))
    with pytest.raises(SchemaNotFoundError, match="Unknown schema"):
        validate_data_against_schema({}, "anything")
