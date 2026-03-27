# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for schema.validate CLI."""

from pathlib import Path

import pytest

from schema.validate import main

KNOWN = "session_state_progress_v1"
_UNKNOWN = "totally_missing_schema_xyz"
_LUNGO_ROOT = Path(__file__).resolve().parents[3]
_EXAMPLES_DIR = _LUNGO_ROOT / "schema" / "jsonschemas" / "examples"
_VALID_INSTANCE = (
    '{"session_id":"s","kind":"snapshot","timestamp":"2026-01-01T00:00:00Z","state":{}}'
)


def test_cli_all_definitions_success(capsys):
    assert main(["all-definitions"]) == 0
    out = capsys.readouterr().out
    assert "All packaged definitions are valid" in out


def test_cli_definition_known_schema_ok(capsys):
    assert main(["definition", KNOWN]) == 0
    assert "ok" in capsys.readouterr().out


def test_cli_definition_unknown_schema(capsys):
    assert main(["definition", _UNKNOWN]) == 1
    assert capsys.readouterr().err.strip()


def test_cli_instances_valid_tmp_file(capsys, tmp_path: Path):
    p = tmp_path / "ok.json"
    p.write_text(_VALID_INSTANCE, encoding="utf-8")
    assert main(["instances", KNOWN, str(p)]) == 0
    assert "ok" in capsys.readouterr().out


def test_cli_instances_packaged_example_snapshot(capsys):
    path = _EXAMPLES_DIR / "session_state_progress_v1_snapshot.json"
    assert main(["instances", KNOWN, str(path)]) == 0


def test_cli_instances_not_a_file(capsys, tmp_path: Path):
    missing = tmp_path / "nope.json"
    assert main(["instances", KNOWN, str(missing)]) == 1
    err = capsys.readouterr().err
    assert "not a file" in err


def test_cli_instances_invalid_json(capsys, tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("{ not json ", encoding="utf-8")
    assert main(["instances", KNOWN, str(p)]) == 1
    assert "invalid instance file" in capsys.readouterr().err


def test_cli_instances_validation_error(capsys, tmp_path: Path):
    p = tmp_path / "empty.json"
    p.write_text("{}", encoding="utf-8")
    assert main(["instances", KNOWN, str(p)]) == 1
    assert capsys.readouterr().err.strip()


def test_cli_instances_multiple_files_partial_failure(capsys, tmp_path: Path):
    good = tmp_path / "good.json"
    good.write_text(_VALID_INSTANCE, encoding="utf-8")
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    code = main(["instances", KNOWN, str(good), str(bad)])
    assert code == 1
    out_err = capsys.readouterr()
    assert "ok" in out_err.out
    assert out_err.err.strip()


def test_cli_instance_string_valid(capsys):
    assert main(["instance-string", KNOWN, _VALID_INSTANCE]) == 0
    assert capsys.readouterr().out.strip() == "ok"


def test_cli_instance_string_invalid_json(capsys):
    assert main(["instance-string", KNOWN, "{broken"]) == 1
    assert "invalid instance payload" in capsys.readouterr().err


def test_cli_instance_string_unknown_schema(capsys):
    assert main(["instance-string", _UNKNOWN, _VALID_INSTANCE]) == 1
    assert capsys.readouterr().err.strip()


def test_cli_instance_string_validation_error(capsys):
    assert main(["instance-string", KNOWN, "{}"]) == 1
    assert capsys.readouterr().err.strip()


def test_cli_get_schema_success(capsys):
    assert main(["get-schema", KNOWN]) == 0
    out = capsys.readouterr().out
    assert "$id" in out or "session_id" in out


def test_cli_get_schema_unknown_schema(capsys):
    assert main(["get-schema", _UNKNOWN]) == 1
    assert capsys.readouterr().err.strip()
