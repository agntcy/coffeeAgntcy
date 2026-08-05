# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Shared helpers for Agentic Workflows hand-maintained OpenAPI contract tests."""

from __future__ import annotations

import ast
import warnings
from pathlib import Path
from typing import Any

import yaml
from prance import ResolvingParser

_LUNGO_ROOT = Path(__file__).resolve().parents[3]
_OPENAPI_ROOT = _LUNGO_ROOT / "schema" / "openapi" / "openapi.yaml"
_AGENTIC_WORKFLOWS_PATHS = (
    _LUNGO_ROOT / "schema" / "openapi" / "paths" / "agentic-workflows.yaml"
)

# Shared components/responses names expected under each HTTP status on operations.
# OpenAPI cannot bind component names to status codes; this convention is enforced in CI.
ERROR_STATUS_TO_RESPONSE_COMPONENT: dict[str, str] = {
    "400": "BadRequest",
    "404": "NotFound",
    "422": "UnprocessableEntity",
    "500": "InternalServerError",
    "503": "ServiceUnavailable",
    "504": "GatewayTimeout",
}

_HTTP_METHODS = frozenset(
    {"get", "post", "put", "patch", "delete", "head", "options", "trace"},
)

_GLOBAL_AUTH_STATUS = "401"


def load_resolved_agentic_workflows_spec() -> dict[str, Any]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        parser = ResolvingParser(str(_OPENAPI_ROOT.resolve()), lazy=True)
        parser.parse()
    spec = parser.specification
    assert isinstance(spec, dict)
    return spec


def status_codes_by_operation_id(spec: dict[str, Any]) -> dict[str, set[str]]:
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
            out[str(operation_id)] = {str(code) for code in responses}
    return out


def all_declared_status_codes(spec: dict[str, Any]) -> set[str]:
    codes: set[str] = set()
    for operation_codes in status_codes_by_operation_id(spec).values():
        codes |= operation_codes
    security = spec.get("security")
    if isinstance(security, list) and security:
        codes.add(_GLOBAL_AUTH_STATUS)
    return codes


def _status_code_from_keyword(keyword: ast.keyword) -> int | None:
    if keyword.arg != "status_code":
        return None
    if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, int):
        return keyword.value.value
    return None


def collect_implemented_http_status_codes(*source_paths: Path) -> set[int]:
    """Literal HTTP status codes set in handler modules (raises, responses, decorators)."""
    codes: set[int] = set()
    for path in source_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                status = _status_code_from_keyword(keyword)
                if status is not None:
                    codes.add(status)
    return codes


def agentic_workflows_implementation_modules() -> list[Path]:
    package = _LUNGO_ROOT / "api" / "agentic_workflows"
    return sorted(package.glob("*.py"))


def load_agentic_workflows_path_items() -> dict[str, Any]:
    """Unresolved path items (preserves response ``$ref`` strings for linting)."""
    document = yaml.safe_load(_AGENTIC_WORKFLOWS_PATHS.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    paths = document.get("paths")
    assert isinstance(paths, dict)
    return paths


def _expected_response_ref_suffix(component_name: str) -> str:
    return f"/components/responses/{component_name}"


def collect_error_response_ref_violations(
    path_items: dict[str, Any] | None = None,
) -> list[str]:
    """Return human-readable violations when status codes use the wrong response ``$ref``."""
    if path_items is None:
        path_items = load_agentic_workflows_path_items()

    violations: list[str] = []
    for path, path_item in sorted(path_items.items()):
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            operation_id = str(operation.get("operationId") or f"{method.upper()} {path}")
            responses = operation.get("responses")
            if not isinstance(responses, dict):
                continue
            for status_code, response in sorted(responses.items()):
                expected_component = ERROR_STATUS_TO_RESPONSE_COMPONENT.get(
                    str(status_code)
                )
                if expected_component is None:
                    continue
                expected_suffix = _expected_response_ref_suffix(expected_component)
                if not isinstance(response, dict):
                    violations.append(
                        f"{operation_id} {status_code}: expected $ref to {expected_component}, "
                        f"got non-object response"
                    )
                    continue
                ref = response.get("$ref")
                if not isinstance(ref, str):
                    violations.append(
                        f"{operation_id} {status_code}: must $ref shared response "
                        f"{expected_component} (inline response not allowed for this status)"
                    )
                    continue
                if not ref.replace("\\", "/").endswith(expected_suffix):
                    violations.append(
                        f"{operation_id} {status_code}: $ref {ref!r} must end with "
                        f"{expected_suffix!r}"
                    )
    return violations
