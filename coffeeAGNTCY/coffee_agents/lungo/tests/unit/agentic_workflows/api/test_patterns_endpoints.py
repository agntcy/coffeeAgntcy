# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the patterns catalog endpoint and root redirect."""

from __future__ import annotations

from typing import NamedTuple

import pytest
from api.agentic_workflows.patterns import PATTERNS
from api.agentic_workflows.router import create_agentic_workflows_router
from api.agentic_workflows.workflow_capabilities import pattern_category_from_workflow
from api.agentic_workflows.workflow_documentation import (
    load_parsed_workflow_documentation,
    pattern_category_from_parsed_documentation,
    workflow_name_to_documentation_slug,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.unit.agentic_workflows.catalog_test_helpers import (
    load_validated_starting_workflows_catalog,
)


@pytest.fixture()
def client(workflow_api_headers: dict[str, str]) -> TestClient:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    with TestClient(app, headers=workflow_api_headers) as test_client:
        yield test_client


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


@pytest.mark.parametrize(
    "case", [pytest.param(c, id=c.case_id) for c in _CASES]
)
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
        assert set(item.keys()) == {"name"}
        assert isinstance(item["name"], str)
        assert len(item["name"]) >= 1

    names = [p["name"] for p in data["items"]]
    assert names == case.outputs.expected_names


# ---------------------------------------------------------------------------
# Reference Library coverage of implemented patterns
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pattern_name", list(PATTERNS))
def test_implemented_pattern_has_reference_library_entry(pattern_name: str) -> None:
    """Implemented patterns are surfaced in the Reference Library too.

    The Reference Library is built from catalog rows marked with ``"---"``, so
    every implemented pattern needs such a row for the sidebar to reach its
    reference material.
    """
    catalog = load_validated_starting_workflows_catalog()

    row = catalog.get(pattern_name)
    assert row is not None, f"{pattern_name!r} has no Reference Library catalog row"
    assert row.pattern == pattern_name
    assert (row.use_case, row.scenario) == ("---", "---")
    assert not row.starting_topology.nodes

    slug = workflow_name_to_documentation_slug(pattern_name)
    parsed = load_parsed_workflow_documentation(slug)
    assert parsed is not None

    # pattern_category decides which Reference Library category the sidebar files
    # the entry under, so it has to agree with the pattern doc and with the
    # runnable workflows of the same pattern.
    documented_category = pattern_category_from_parsed_documentation(parsed)
    assert documented_category is not None, f"{slug}.md declares no category"
    assert pattern_category_from_workflow(row) == documented_category

    runnable_categories = {
        pattern_category_from_workflow(wf)
        for wf in catalog.values()
        if wf.pattern == pattern_name and (wf.use_case, wf.scenario) != ("---", "---")
    }
    assert runnable_categories == {documented_category}
