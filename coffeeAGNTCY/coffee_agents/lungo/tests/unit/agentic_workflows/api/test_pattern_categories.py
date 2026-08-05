# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for pattern category catalog and markdown parsing."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from api.agentic_workflows.pattern_categories import PATTERN_CATEGORIES
from api.agentic_workflows.pattern_category_documentation import (
    load_pattern_category_documentation,
)
from api.agentic_workflows.router import create_agentic_workflows_router
from api.agentic_workflows.workflow_capabilities import (
    derive_workflow_catalog_summary_fields,
    pattern_category_from_workflow,
)
from api.agentic_workflows.workflow_documentation import (
    load_parsed_workflow_documentation,
    parse_pattern_category_from_section_body,
    pattern_category_from_parsed_documentation,
)
from api.agentic_workflows.workflows import (
    _load_and_validate_starting_workflows_from_file,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.unit.agentic_workflows.catalog_test_helpers import STARTING_WORKFLOWS_JSON


def test_pattern_categories_loaded_from_category_docs() -> None:
    assert len(PATTERN_CATEGORIES) == 9
    assert "Internet of Cognition" in PATTERN_CATEGORIES
    assert "Orchestration & Control Flow" in PATTERN_CATEGORIES


def test_starting_workflows_catalog_has_pattern_category_on_every_entry() -> None:
    catalog = _load_and_validate_starting_workflows_from_file(STARTING_WORKFLOWS_JSON)
    assert catalog
    for wf in catalog.values():
        category = pattern_category_from_workflow(wf)
        assert category, f"{wf.name!r} missing pattern_category"
        _, supports_sse, supports_streaming, chat_api_target = (
            derive_workflow_catalog_summary_fields(wf)
        )
        assert isinstance(supports_sse, bool)
        assert isinstance(supports_streaming, bool)
        assert category in PATTERN_CATEGORIES


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (
            "**References:**\n\n- x\n\n**Category:** Internet of Cognition\n",
            "Internet of Cognition",
        ),
        (
            "**Category:** Orchestration & Control Flow\n\nBody",
            "Orchestration & Control Flow",
        ),
        ("No category here", None),
    ],
)
def test_parse_pattern_category_from_section_body(
    body: str, expected: str | None
) -> None:
    assert parse_pattern_category_from_section_body(body) == expected


def test_publish_subscribe_documentation_pattern_category() -> None:
    parsed = load_parsed_workflow_documentation("publish_subscribe")
    assert parsed is not None
    assert pattern_category_from_parsed_documentation(parsed) == (
        "Orchestration & Control Flow"
    )


def test_load_pattern_category_documentation() -> None:
    parsed = load_pattern_category_documentation("Orchestration & Control Flow")
    assert parsed is not None
    assert parsed.slug == "orchestration_and_control_flow"
    assert parsed.title == "Orchestration & Control Flow"
    assert parsed.full_markdown.startswith("# Orchestration & Control Flow")
    assert "coordinator at the centre" in parsed.full_markdown


@pytest.fixture()
def categories_client(workflow_api_headers: dict[str, str]) -> TestClient:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    with (
        patch(
            "api.agentic_workflows.router.get_workflows",
            return_value={},
        ),
        TestClient(app, headers=workflow_api_headers) as test_client,
    ):
        yield test_client


def test_list_pattern_categories(categories_client: TestClient) -> None:
    resp = categories_client.get("/pattern-categories/")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    names = [item["name"] for item in data["items"]]
    assert names == PATTERN_CATEGORIES
    assert set(names) == set(PATTERN_CATEGORIES)
    for item in data["items"]:
        assert set(item.keys()) == {"name"}


def test_get_pattern_category_documentation(categories_client: TestClient) -> None:
    category_name = "Orchestration & Control Flow"
    resp = categories_client.get(
        f"/pattern-categories/{category_name}/documentation/"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == category_name
    assert data["slug"] == "orchestration_and_control_flow"
    assert data["title"] == category_name
    assert data["full_markdown"].startswith(f"# {category_name}")
    assert "coordinator at the centre" in data["full_markdown"]


def test_get_pattern_category_documentation_not_found(
    categories_client: TestClient,
) -> None:
    resp = categories_client.get("/pattern-categories/Unknown Category/documentation/")
    assert resp.status_code == 404
