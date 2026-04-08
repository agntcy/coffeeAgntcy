# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the use-cases catalog endpoint."""

from __future__ import annotations

import pytest
from api.agentic_workflows.router import create_agentic_workflows_router
from api.agentic_workflows.use_cases import USE_CASES
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /use-cases/
# ---------------------------------------------------------------------------


class TestListUseCases:
    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get("/use-cases/")
        assert resp.status_code == 200

    def test_response_has_items_key(self, client: TestClient) -> None:
        data = client.get("/use-cases/").json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_each_item_has_name(self, client: TestClient) -> None:
        items = client.get("/use-cases/").json()["items"]
        for item in items:
            assert "name" in item
            assert isinstance(item["name"], str)
            assert len(item["name"]) >= 1

    def test_no_extra_fields_on_items(self, client: TestClient) -> None:
        items = client.get("/use-cases/").json()["items"]
        for item in items:
            assert set(item.keys()) == {"name"}

    def test_names_match_catalog(self, client: TestClient) -> None:
        names = [u["name"] for u in client.get("/use-cases/").json()["items"]]
        assert names == USE_CASES
