# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the patterns catalog endpoint and root redirect."""

from __future__ import annotations

from typing import NamedTuple

import pytest
from api.agentic_workflows.patterns import PATTERNS
from api.agentic_workflows.router import create_agentic_workflows_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    return TestClient(app)


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
