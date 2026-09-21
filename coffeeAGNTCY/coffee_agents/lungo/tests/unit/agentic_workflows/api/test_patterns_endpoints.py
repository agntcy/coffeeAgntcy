# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the pattern reference library endpoints and root redirect."""

from __future__ import annotations

from typing import NamedTuple
from unittest.mock import patch

import pytest
from api.agentic_workflows.pattern_categories import PATTERN_CATEGORIES
from api.agentic_workflows.pattern_documentation import load_pattern_documentation
from api.agentic_workflows.patterns import (
    PATTERN_BY_NAME,
    PATTERN_RECORDS,
    PATTERNS,
    _load_pattern_records,
    implemented_pattern_names,
)
from api.agentic_workflows.router import create_agentic_workflows_router
from api.agentic_workflows.workflows import (
    _load_and_validate_starting_workflows_from_file,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.unit.agentic_workflows.catalog_test_helpers import STARTING_WORKFLOWS_JSON

# Patterns that the workflow catalog backs with at least one runnable workflow.
_IMPLEMENTED_PATTERNS = frozenset({"Supervisor", "Peer Group", "Recruiter"})


@pytest.fixture()
def catalog() -> dict:
    return _load_and_validate_starting_workflows_from_file(STARTING_WORKFLOWS_JSON)


@pytest.fixture()
def client(workflow_api_headers: dict[str, str], catalog: dict) -> TestClient:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    with (
        patch(
            "api.agentic_workflows.router.get_workflows",
            return_value=catalog,
        ),
        TestClient(app, headers=workflow_api_headers) as test_client,
    ):
        yield test_client


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def test_registry_is_derived_from_every_pattern_doc() -> None:
    """Every markdown file under docs/patterns yields exactly one record."""
    from api.agentic_workflows.patterns import PATTERN_DOCS_DIR

    doc_slugs = {path.stem for path in PATTERN_DOCS_DIR.glob("*.md")}
    assert doc_slugs, "docs/patterns must not be empty"
    assert {record.slug for record in PATTERN_RECORDS} == doc_slugs


def test_registry_is_sorted_by_name_and_uses_known_categories() -> None:
    assert PATTERNS == sorted(PATTERNS)
    assert len(PATTERN_BY_NAME) == len(PATTERN_RECORDS), "pattern names must be unique"
    for record in PATTERN_RECORDS:
        assert record.pattern_category in PATTERN_CATEGORIES


@pytest.mark.parametrize(
    "markdown",
    [
        "No heading\n\n**Category:** Orchestration & Control Flow\n",
        "# Missing Category\n",
        "# Empty Category\n\n**Category:**\n",
        "# Unknown Category\n\n**Category:** Not a real category\n",
    ],
)
def test_registry_rejects_invalid_pattern_docs(tmp_path, markdown: str) -> None:
    (tmp_path / "invalid.md").write_text(markdown, encoding="utf-8")

    with pytest.raises(ValueError):
        _load_pattern_records(tmp_path)


def test_registry_rejects_duplicate_pattern_names(tmp_path) -> None:
    markdown = "# Duplicate\n\n**Category:** Orchestration & Control Flow\n"
    (tmp_path / "first.md").write_text(markdown, encoding="utf-8")
    (tmp_path / "second.md").write_text(markdown, encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate pattern name"):
        _load_pattern_records(tmp_path)


def test_registry_rejects_empty_docs_directory(tmp_path) -> None:
    with pytest.raises(ValueError, match="directory is empty"):
        _load_pattern_records(tmp_path)


def test_implemented_patterns_are_part_of_the_reference_library(catalog: dict) -> None:
    """The library is the full set: implemented patterns are listed too (#660)."""
    implemented = implemented_pattern_names(catalog)
    assert implemented == _IMPLEMENTED_PATTERNS
    assert implemented <= set(PATTERNS)


# ---------------------------------------------------------------------------
# GET /patterns/ and GET / (redirect)
# ---------------------------------------------------------------------------


class Inputs(NamedTuple):
    path: str
    follow_redirects: bool


class Outputs(NamedTuple):
    status: int
    expected_names: list[str] | None
    redirect_location: str | None


class Case(NamedTuple):
    case_id: str
    inputs: Inputs
    outputs: Outputs


_CASES: tuple[Case, ...] = (
    Case(
        case_id="list_patterns_returns_catalog",
        inputs=Inputs(path="/patterns/", follow_redirects=True),
        outputs=Outputs(
            status=200,
            expected_names=list(PATTERNS),
            redirect_location=None,
        ),
    ),
    Case(
        case_id="root_redirects_to_patterns",
        inputs=Inputs(path="/", follow_redirects=False),
        outputs=Outputs(
            status=307,
            expected_names=None,
            redirect_location="/patterns/",
        ),
    ),
    Case(
        case_id="root_following_redirect_returns_patterns",
        inputs=Inputs(path="/", follow_redirects=True),
        outputs=Outputs(
            status=200,
            expected_names=list(PATTERNS),
            redirect_location=None,
        ),
    ),
)


@pytest.mark.parametrize("case", [pytest.param(c, id=c.case_id) for c in _CASES])
def test_patterns_endpoint(case: Case, client: TestClient) -> None:
    resp = client.get(
        case.inputs.path,
        follow_redirects=case.inputs.follow_redirects,
    )
    assert resp.status_code == case.outputs.status

    if case.outputs.redirect_location is not None:
        assert resp.headers["location"] == case.outputs.redirect_location
        return

    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)

    for item in data["items"]:
        assert set(item.keys()) == {"name", "pattern_category", "implemented"}
        assert isinstance(item["name"], str)
        assert len(item["name"]) >= 1
        assert item["pattern_category"] in PATTERN_CATEGORIES
        assert isinstance(item["implemented"], bool)

    names = [p["name"] for p in data["items"]]
    assert names == case.outputs.expected_names

    implemented = {p["name"] for p in data["items"] if p["implemented"]}
    assert implemented == _IMPLEMENTED_PATTERNS


def test_list_patterns_without_catalog_marks_nothing_implemented(
    workflow_api_headers: dict[str, str],
) -> None:
    """The catalog is not loaded before startup; the library still lists everything."""
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    with (
        patch("api.agentic_workflows.router.get_workflows", return_value=None),
        TestClient(app, headers=workflow_api_headers) as test_client,
    ):
        resp = test_client.get("/patterns/")

    assert resp.status_code == 200
    items = resp.json()["items"]
    assert [item["name"] for item in items] == list(PATTERNS)
    assert not any(item["implemented"] for item in items)


# ---------------------------------------------------------------------------
# GET /patterns/{name}/documentation/
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("identifier", ["Feedback Loop", "feedback loop", "feedback_loop"])
def test_load_pattern_documentation_resolves_name_and_legacy_aliases(
    identifier: str,
) -> None:
    parsed = load_pattern_documentation(identifier)
    assert parsed is not None
    assert parsed.slug == "feedback_loop"
    assert parsed.name == "Feedback Loop"
    assert parsed.title == "Feedback Loop"
    assert parsed.pattern_category == "Learning, Feedback & Self-Improvement"
    assert parsed.full_markdown.startswith("# Feedback Loop")


@pytest.mark.parametrize(
    "pattern_name",
    ["Unknown Pattern", "../workflows/publish_subscribe", ""],
)
def test_load_pattern_documentation_rejects_unknown_names(pattern_name: str) -> None:
    assert load_pattern_documentation(pattern_name) is None


@pytest.mark.parametrize(
    ("pattern_name", "slug", "implemented"),
    [
        pytest.param("Supervisor", "supervisor", True, id="implemented"),
        pytest.param("Feedback Loop", "feedback_loop", False, id="reference_only"),
    ],
)
def test_get_pattern_documentation(
    client: TestClient, pattern_name: str, slug: str, implemented: bool
) -> None:
    resp = client.get(f"/patterns/{pattern_name}/documentation/")
    assert resp.status_code == 200

    data = resp.json()
    assert data["name"] == pattern_name
    assert data["slug"] == slug
    assert data["title"] == pattern_name
    assert data["implemented"] is implemented
    assert data["pattern_category"] == PATTERN_BY_NAME[pattern_name].pattern_category
    assert data["full_markdown"].startswith(f"# {pattern_name}")


def test_get_pattern_documentation_not_found(client: TestClient) -> None:
    resp = client.get("/patterns/Definitely Not A Pattern/documentation/")
    assert resp.status_code == 404


def test_get_pattern_documentation_accepts_legacy_slug(client: TestClient) -> None:
    resp = client.get("/patterns/feedback_loop/documentation/")

    assert resp.status_code == 200
    assert resp.json()["name"] == "Feedback Loop"


def test_get_pattern_documentation_does_not_serve_workflow_docs(
    client: TestClient,
) -> None:
    """Workflow markdown stays behind the workflow endpoint (#660 separation)."""
    resp = client.get("/patterns/Publish Subscribe/documentation/")
    assert resp.status_code == 404


def test_every_pattern_has_reachable_documentation(client: TestClient) -> None:
    for name in PATTERNS:
        resp = client.get(f"/patterns/{name}/documentation/")
        assert resp.status_code == 200, f"{name!r} has no reachable reference doc"
