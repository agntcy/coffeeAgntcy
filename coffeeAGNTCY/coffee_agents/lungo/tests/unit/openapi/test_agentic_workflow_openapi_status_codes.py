# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Hand-maintained OpenAPI is the HTTP status contract; implementation must conform."""

from __future__ import annotations

import pytest

from tests.unit.openapi.openapi_spec_helpers import (
    agentic_workflows_implementation_modules,
    all_declared_status_codes,
    collect_error_response_ref_violations,
    collect_implemented_http_status_codes,
    load_resolved_agentic_workflows_spec,
    status_codes_by_operation_id,
)


@pytest.mark.filterwarnings("ignore::UserWarning:requests")
def test_agentic_workflows_openapi_declares_global_bearer_security() -> None:
    spec = load_resolved_agentic_workflows_spec()
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
def test_agentic_workflows_openapi_operations_declare_responses() -> None:
    spec = load_resolved_agentic_workflows_spec()
    by_op = status_codes_by_operation_id(spec)
    assert by_op, "expected at least one operation with operationId in OpenAPI paths"
    missing: list[str] = []
    for operation_id, codes in sorted(by_op.items()):
        if not codes:
            missing.append(operation_id)
    assert not missing, (
        "Every operation must declare at least one response in OpenAPI: "
        + ", ".join(missing)
    )


@pytest.mark.filterwarnings("ignore::UserWarning:requests")
def test_agentic_workflows_implementation_status_codes_declared_in_openapi() -> None:
    """Handler/auth modules may only use status codes published in schema/openapi/."""
    spec = load_resolved_agentic_workflows_spec()
    declared = all_declared_status_codes(spec)
    implemented = collect_implemented_http_status_codes(
        *agentic_workflows_implementation_modules()
    )
    # FastAPI emits 422 for request validation; handlers do not raise it explicitly.
    declared_with_validation = declared | {"422"}

    undeclared = sorted(
        str(code) for code in implemented if str(code) not in declared_with_validation
    )
    assert not undeclared, (
        "Implementation uses HTTP status codes not declared in OpenAPI "
        f"(schema/openapi/): {undeclared}. "
        f"Declared union: {sorted(declared_with_validation)}"
    )


@pytest.mark.filterwarnings("ignore::UserWarning:requests")
def test_agentic_workflows_openapi_error_responses_match_status_convention() -> None:
    """Declared error statuses must $ref the matching components/responses name."""
    violations = collect_error_response_ref_violations()
    assert not violations, "OpenAPI error response $ref mismatches:\n" + "\n".join(
        violations
    )
