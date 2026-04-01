# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for schema.json_schema (JSON Schema packaged backend mechanics)."""

import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest

from schema import json_schema as json_schema_mod
from schema.errors import (
    AmbiguousSchemaNameError,
    InstanceDecodeError,
    SchemaDefinitionError,
    SchemaNotFoundError,
    SchemaValidationError,
)

_PACKAGED_JSONSCHEMAS = Path(__file__).resolve().parents[3] / "schema" / "jsonschemas"
from schema.json_schema import (
    JsonSchemaPackagedBackend,
    clear_event_type_v1_cache,
    get_schema,
    is_event_type_registered,
    load_event_type_registry,
    load_json_instance_file,
    packaged_json_schema_backend,
    parse_json_instance_text,
    resolve_json_schema_path,
    validate_all_json_schema_definitions,
    validate_json_instance,
    validate_json_schema_definition,
)


@pytest.fixture(autouse=True)
def _clear_event_type_v1_cache_after_each_test():
    yield
    clear_event_type_v1_cache()


@pytest.fixture
def json_schema_specs_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setattr(json_schema_mod, "_JSONSCHEMA_SPECS_DIR", tmp_path)
    return tmp_path


@dataclass
class GetSchemaCase:
    schema_name: str
    expect_error: bool
    match: str


_GET_SCHEMA_CASES = [
    pytest.param(
        GetSchemaCase(
            schema_name="event_v1",
            expect_error=False,
            match="event_v1.json",
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
        with pytest.raises(SchemaNotFoundError, match=case.match):
            get_schema(case.schema_name)
    else:
        schema = get_schema(case.schema_name)
        assert schema.get("$id", "").endswith(case.match)


@pytest.mark.parametrize("case", _GET_SCHEMA_CASES)
def test_resolve_json_schema_path_matches_get_schema_errors(case: GetSchemaCase):
    if case.expect_error:
        with pytest.raises(SchemaNotFoundError, match=case.match):
            resolve_json_schema_path(case.schema_name)
    else:
        path = resolve_json_schema_path(case.schema_name)
        assert path.name == case.match


def test_resolve_json_schema_path_ambiguous(json_schema_specs_dir: Path):
    (json_schema_specs_dir / "foo.json").write_text("{}", encoding="utf-8")
    (json_schema_specs_dir / "foo_bar.json").write_text("{}", encoding="utf-8")
    with pytest.raises(AmbiguousSchemaNameError, match="Ambiguous"):
        resolve_json_schema_path("foo")


def test_get_schema_invalid_json_in_schema_file(json_schema_specs_dir: Path):
    (json_schema_specs_dir / "broken.json").write_text("{ not json ", encoding="utf-8")
    with pytest.raises(SchemaDefinitionError) as exc_info:
        get_schema("broken")
    assert exc_info.value.path is not None
    assert exc_info.value.path.name == "broken.json"


@dataclass
class ValidateJsonSchemaDefinitionCase:
    description: str
    filename: str
    content: str
    expect_error_substring: str | None


_VALIDATE_JSON_SCHEMA_DEF_CASES = [
    pytest.param(
        ValidateJsonSchemaDefinitionCase(
            description="valid minimal draft 2020-12 object",
            filename="ok.json",
            content='{"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"}',
            expect_error_substring=None,
        ),
        id="valid_schema",
    ),
    pytest.param(
        ValidateJsonSchemaDefinitionCase(
            description="invalid type keyword",
            filename="bad.json",
            content='{"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "not_a_real_type"}',
            expect_error_substring="not_a_real_type",
        ),
        id="invalid_type",
    ),
]


@pytest.mark.parametrize("case", _VALIDATE_JSON_SCHEMA_DEF_CASES)
def test_validate_json_schema_definition_on_disk(
    json_schema_specs_dir: Path,
    case: ValidateJsonSchemaDefinitionCase,
):
    (json_schema_specs_dir / case.filename).write_text(case.content)
    stem = case.filename.removesuffix(".json")
    if case.expect_error_substring is None:
        path = validate_json_schema_definition(stem)
        assert path.name == case.filename
    else:
        with pytest.raises(SchemaDefinitionError) as exc_info:
            validate_json_schema_definition(stem)
        assert case.expect_error_substring in str(exc_info.value)


def test_get_schema_ambiguous_name_raises(json_schema_specs_dir: Path):
    (json_schema_specs_dir / "event_v1.json").write_text("{}")
    (json_schema_specs_dir / "event_v1_alt.json").write_text("{}")
    with pytest.raises(AmbiguousSchemaNameError, match="Ambiguous"):
        get_schema("event_v1")


@dataclass
class BadSchemaFileCase:
    filename: str
    content: str
    expected_in_error: str


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
def test_validate_all_json_schema_definitions_detects_failures(
    json_schema_specs_dir: Path,
    case: BadSchemaFileCase,
):
    (json_schema_specs_dir / case.filename).write_text(case.content)
    failures = validate_all_json_schema_definitions()
    assert len(failures) == 1
    assert failures[0].path is not None
    assert failures[0].path.name == case.filename
    assert case.expected_in_error in str(failures[0])


def test_validate_all_json_schema_definitions_empty_dir_returns_empty(json_schema_specs_dir: Path):
    assert validate_all_json_schema_definitions() == []


def test_validate_all_json_schema_definitions_multiple_failures(json_schema_specs_dir: Path):
    (json_schema_specs_dir / "a.json").write_text('{"type": "nope"}')
    (json_schema_specs_dir / "b.json").write_text("not json at all")
    failures = validate_all_json_schema_definitions()
    assert len(failures) == 2
    paths = {f.path.name for f in failures if f.path}
    assert paths == {"a.json", "b.json"}


def test_validate_all_json_schema_definitions_packaged_dir_passes():
    assert validate_all_json_schema_definitions() == []


_MINIMAL_OBJECT_SCHEMA = (
    '{"$schema": "https://json-schema.org/draft/2020-12/schema", '
    '"type": "object", "properties": {"n": {"type": "integer"}}, "required": ["n"]}'
)


_MINIMAL_EVENT_TYPE_V1 = (
    '{"$schema": "https://json-schema.org/draft/2020-12/schema",'
    '"$id": "https://example.test/schema/event_type_v1.json",'
    '"$defs": {"event_type": {"type": "string", "enum": ["A"]}}}'
)


def test_validate_all_includes_event_type_v1_file(json_schema_specs_dir: Path):
    (json_schema_specs_dir / "event_type_v1.json").write_text(
        _MINIMAL_EVENT_TYPE_V1, encoding="utf-8"
    )
    (json_schema_specs_dir / "only.json").write_text(_MINIMAL_OBJECT_SCHEMA)
    assert validate_all_json_schema_definitions() == []


@dataclass
class LoadEventTypeRegistryFailCase:
    content: str
    substring: str


_LOAD_EVENT_TYPE_REGISTRY_FAIL_CASES = [
    pytest.param(
        LoadEventTypeRegistryFailCase("{ not json ", "invalid json"),
        id="invalid_json",
    ),
    pytest.param(
        LoadEventTypeRegistryFailCase("[]", "json schema object"),
        id="not_object",
    ),
    pytest.param(
        LoadEventTypeRegistryFailCase(
            '{"$id": "https://example.test/r.json"}',
            "$defs",
        ),
        id="missing_defs",
    ),
    pytest.param(
        LoadEventTypeRegistryFailCase(
            '{"$id": "https://example.test/r.json", "$defs": {}}',
            "event_type",
        ),
        id="missing_event_type_def",
    ),
    pytest.param(
        LoadEventTypeRegistryFailCase(
            '{"$id": "https://example.test/r.json",'
            '"$defs": {"event_type": {"type": "string", "enum": []}}}',
            "non-empty",
        ),
        id="empty_enum",
    ),
    pytest.param(
        LoadEventTypeRegistryFailCase(
            '{"$id": "https://example.test/r.json",'
            '"$defs": {"event_type": {"type": "string", "enum": [1]}}}',
            "only strings",
        ),
        id="enum_non_string",
    ),
    pytest.param(
        LoadEventTypeRegistryFailCase(
            '{"$defs": {"event_type": {"type": "string", "enum": ["A"]}}}',
            "$id",
        ),
        id="missing_id",
    ),
]


@pytest.mark.parametrize("case", _LOAD_EVENT_TYPE_REGISTRY_FAIL_CASES)
def test_load_event_type_registry_invalid_documents(
    json_schema_specs_dir: Path,
    case: LoadEventTypeRegistryFailCase,
):
    clear_event_type_v1_cache()
    (json_schema_specs_dir / "event_type_v1.json").write_text(
        case.content, encoding="utf-8"
    )
    with pytest.raises(SchemaDefinitionError) as exc_info:
        load_event_type_registry()
    assert case.substring.lower() in str(exc_info.value).lower()
    assert exc_info.value.path is not None
    assert exc_info.value.path.name == "event_type_v1.json"


def test_load_event_type_registry_packaged():
    types = load_event_type_registry()
    assert isinstance(types, list) and all(isinstance(t, str) for t in types)
    assert "RecruiterNodeSearch" in types
    assert len(types) == len(set(types))


def test_is_event_type_registered_packaged():
    assert is_event_type_registered("RecruiterNodeSearch") is True
    assert is_event_type_registered("UnknownEventType_xyz") is False


def test_validate_json_instance_valid_and_invalid(json_schema_specs_dir: Path):
    (json_schema_specs_dir / "num.json").write_text(_MINIMAL_OBJECT_SCHEMA)
    validate_json_instance({"n": 1}, "num")
    with pytest.raises(SchemaValidationError):
        validate_json_instance({}, "num")


def test_validate_json_instance_unresolvable_ref_maps_to_schema_validation_error(
    json_schema_specs_dir: Path,
):
    """Reference resolution failures (referencing.Unresolvable) map like constraint failures."""
    bad_ref_schema = (
        '{"$schema": "https://json-schema.org/draft/2020-12/schema",'
        '"type": "object",'
        '"properties": {"x": {"$ref": "https://example.invalid/unresolvable.json"}},'
        '"required": ["x"]}'
    )
    (json_schema_specs_dir / "bad_ref.json").write_text(bad_ref_schema, encoding="utf-8")
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_json_instance({"x": 1}, "bad_ref")
    msg = str(exc_info.value).lower()
    assert "unresolvable" in msg or "example.invalid" in msg


def test_validate_json_instance_event_type_v1_corrupt_raises_schema_definition_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    clear_event_type_v1_cache()
    shutil.copy2(
        _PACKAGED_JSONSCHEMAS / "event_v1.json",
        tmp_path / "event_v1.json",
    )
    shutil.copy2(
        _PACKAGED_JSONSCHEMAS / "event_type_v1.json",
        tmp_path / "event_type_v1.json",
    )
    monkeypatch.setattr(json_schema_mod, "_JSONSCHEMA_SPECS_DIR", tmp_path)
    (tmp_path / "event_type_v1.json").write_text("{}", encoding="utf-8")
    clear_event_type_v1_cache()
    minimal = {
        "metadata": {
            "timestamp": "2026-01-01T00:00:00Z",
            "schema_version": "1.0.0",
            "correlation": {"id": "correlation://550e8400-e29b-41d4-a716-446655440001"},
            "id": "event://550e8400-e29b-41d4-a716-446655440002",
            "type": "RecruiterNodeSearch",
            "source": "t",
        },
        "data": {
            "workflows": {
                "w": {
                    "pattern": "p",
                    "use_case": "u",
                    "name": "n",
                    "starting_topology": {"nodes": [], "edges": []},
                    "instances": {
                        "instance://550e8400-e29b-41d4-a716-446655440003": {
                            "id": "instance://550e8400-e29b-41d4-a716-446655440003",
                            "topology": {},
                        }
                    },
                }
            }
        },
    }
    with pytest.raises(SchemaDefinitionError) as exc_info:
        validate_json_instance(minimal, "event_v1")
    err = str(exc_info.value).lower()
    assert "event_type_v1" in err or "$id" in str(exc_info.value)


@pytest.mark.parametrize(
    "load_kind,path_or_text,expect_match",
    [
        pytest.param("file", "{}", None, id="file_valid_object"),
        pytest.param("file", "{ not json ", "Expecting", id="file_invalid_json"),
        pytest.param("text", '{"x": 1}', None, id="text_valid_object"),
        pytest.param("text", "[", "Expecting", id="text_invalid_json"),
    ],
)
def test_load_and_parse_instance_json(
    json_schema_specs_dir: Path,
    load_kind: str,
    path_or_text: str,
    expect_match: str | None,
):
    if load_kind == "file":
        p = json_schema_specs_dir / "inst.json"
        p.write_text(path_or_text, encoding="utf-8")
        if expect_match:
            with pytest.raises(InstanceDecodeError, match=expect_match):
                load_json_instance_file(p)
        else:
            assert load_json_instance_file(p) == {}
    else:
        if expect_match:
            with pytest.raises(InstanceDecodeError, match=expect_match):
                parse_json_instance_text(path_or_text)
        else:
            assert parse_json_instance_text(path_or_text) == {"x": 1}


@pytest.mark.parametrize(
    "method_name,args,expected_calls",
    [
        pytest.param(
            "validate_definition",
            ("stem",),
            [("validate_json_schema_definition", ("stem",))],
            id="validate_definition_delegates",
        ),
        pytest.param(
            "get_schema",
            ("stem",),
            [("get_schema", ("stem",))],
            id="get_schema_delegates",
        ),
    ],
)
def test_json_schema_packaged_backend_delegates(monkeypatch, method_name, args, expected_calls):
    recorded: list[tuple[str, tuple]] = []

    def record(name):
        def _fn(*a):
            recorded.append((name, a))
            if name == "validate_json_schema_definition":
                return Path("/fake/path.json")
            if name == "get_schema":
                return {"k": 1}
            raise AssertionError(name)

        return _fn

    monkeypatch.setattr(
        json_schema_mod,
        "validate_json_schema_definition",
        record("validate_json_schema_definition"),
    )
    monkeypatch.setattr(json_schema_mod, "get_schema", record("get_schema"))

    backend = JsonSchemaPackagedBackend()
    getattr(backend, method_name)(*args)

    assert recorded == expected_calls


def test_json_schema_packaged_backend_validate_data_delegates(monkeypatch):
    called: list[tuple] = []

    def capture(instance, name):
        called.append((instance, name))

    monkeypatch.setattr(json_schema_mod, "validate_json_instance", capture)
    backend = JsonSchemaPackagedBackend()
    backend.validate_data({"a": 1}, "s")
    assert called == [({"a": 1}, "s")]


def test_json_schema_packaged_backend_parse_delegates(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        json_schema_mod,
        "load_json_instance_file",
        lambda p: {"from": "file", "p": str(p)},
    )
    monkeypatch.setattr(
        json_schema_mod,
        "parse_json_instance_text",
        lambda t: {"from": "text", "t": t},
    )
    backend = JsonSchemaPackagedBackend()
    p = tmp_path / "x.json"
    p.write_text("{}", encoding="utf-8")
    assert backend.parse_instance_file(p)["from"] == "file"
    assert backend.parse_instance_text("{}")["from"] == "text"


def test_json_schema_packaged_backend_owns_schema_true_false(json_schema_specs_dir: Path):
    backend = JsonSchemaPackagedBackend()
    assert backend.owns_schema("nope_not_a_schema") is False
    (json_schema_specs_dir / "only.json").write_text(_MINIMAL_OBJECT_SCHEMA)
    assert backend.owns_schema("only") is True


def test_packaged_backend_singleton_is_definition_backend_instance():
    assert isinstance(packaged_json_schema_backend, JsonSchemaPackagedBackend)
