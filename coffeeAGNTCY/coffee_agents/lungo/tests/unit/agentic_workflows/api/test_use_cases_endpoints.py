# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the use-cases catalog endpoint."""

from __future__ import annotations

from typing import NamedTuple

import pytest
from api.agentic_workflows.router import create_agentic_workflows_router
from api.agentic_workflows.use_cases import USE_CASES
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# GET /use-cases/
# ---------------------------------------------------------------------------


class Inputs(NamedTuple):
    path: str


class Outputs(NamedTuple):
    status: int
    expected_names: list[str]


class Case(NamedTuple):
    case_id: str
    inputs: Inputs
    outputs: Outputs


_CASES: tuple[Case, ...] = (
    Case(
        case_id="list_use_cases_returns_catalog",
        inputs=Inputs(path="/use-cases/"),
        outputs=Outputs(
            status=200,
            expected_names=list(USE_CASES),
        ),
    ),
)


@pytest.mark.parametrize(
    "case", [pytest.param(c, id=c.case_id) for c in _CASES]
)
def test_use_cases_endpoint(case: Case, client: TestClient) -> None:
    resp = client.get(case.inputs.path)
    assert resp.status_code == case.outputs.status

    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)

    for item in data["items"]:
        assert set(item.keys()) == {"name"}
        assert isinstance(item["name"], str)
        assert len(item["name"]) >= 1

    names = [u["name"] for u in data["items"]]
    assert names == case.outputs.expected_names
