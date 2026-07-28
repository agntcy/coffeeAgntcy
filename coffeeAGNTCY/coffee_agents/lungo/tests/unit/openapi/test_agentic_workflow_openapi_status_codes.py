# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Curated HTTP status manifest is declared on each Agentic Workflows OpenAPI operation."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import pytest
import yaml
from prance import ResolvingParser

_LUNGO_ROOT = Path(__file__).resolve().parents[3]
_OPENAPI_ROOT = _LUNGO_ROOT / "schema" / "openapi" / "openapi.yaml"
_STATUS_MANIFEST = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "agentic_workflows_expected_status_codes.yaml"
)

_HTTP_METHODS = frozenset(
    {"get", "post", "put", "patch", "delete", "head", "options", "trace"},
)

_GLOBAL_AUTH_STATUS = "401"


def _load_resolved_spec() -> dict[str, Any]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        parser = ResolvingParser(str(_OPENAPI_ROOT.resolve()), lazy=True)
        parser.parse()
    spec = parser.specification
    assert isinstance(spec, dict)
    return spec


def _load_status_manifest() -> dict[str, list[str]]:
    raw = yaml.safe_load(_STATUS_MANIFEST.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    by_op = raw.get("operationId")
    assert isinstance(by_op, dict)
    return {str(op_id): list(codes) for op_id, codes in by_op.items()}


def _status_codes_by_operation_id(spec: dict[str, Any]) -> dict[str, set[str]]:
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return {}
    out: dict[str, set[str]] = {}
    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if not operation_id:
                continue
            responses = operation.get("responses")
            if not isinstance(responses, dict):
                responses = {}
            codes = {str(code) for code in responses}
            out[str(operation_id)] = codes
    return out


@pytest.mark.filterwarnings("ignore::UserWarning:requests")
def test_agentic_workflows_openapi_declares_global_bearer_security() -> None:
    spec = _load_resolved_spec()
    security = spec.get("security")
    assert security == [{"WorkflowApiKeyBearer": []}], (
        "openapi.yaml must declare global WorkflowApiKeyBearer security (401)"
    )
    components = spec.get("components")
    assert isinstance(components, dict)
    schemes = components.get("securitySchemes")
    assert isinstance(schemes, dict)
    assert "WorkflowApiKeyBearer" in schemes


@pytest.mark.filterwarnings("ignore::UserWarning:requests")
def test_agentic_workflows_openapi_status_codes_match_manifest() -> None:
    spec = _load_resolved_spec()
    manifest = _load_status_manifest()
    declared = _status_codes_by_operation_id(spec)

    missing_ops = sorted(set(manifest) - set(declared))
    assert not missing_ops, (
        "OpenAPI is missing operationId(s) from the status manifest: "
        f"{missing_ops}"
    )

    failures: list[str] = []
    for operation_id, expected_codes in sorted(manifest.items()):
        op_declared = declared.get(operation_id, set())
        for code in expected_codes:
            if code == _GLOBAL_AUTH_STATUS:
                continue
            if code not in op_declared:
                failures.append(
                    f"{operation_id}: manifest expects {code} but OpenAPI "
                    f"declares {sorted(op_declared)}"
                )

    assert not failures, "Status code drift:\n" + "\n".join(failures)
