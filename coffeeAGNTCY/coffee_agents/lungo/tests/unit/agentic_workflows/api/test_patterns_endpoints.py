# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the patterns catalog endpoint."""

from __future__ import annotations

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
# GET /patterns/
# ---------------------------------------------------------------------------


class TestListPatterns:
    def test_returns_200(self, client: TestClient) -> None:
        resp = client.get("/patterns/")
        assert resp.status_code == 200

    def test_response_has_items_key(self, client: TestClient) -> None:
        data = client.get("/patterns/").json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_each_item_has_name(self, client: TestClient) -> None:
        items = client.get("/patterns/").json()["items"]
        for item in items:
            assert "name" in item
            assert isinstance(item["name"], str)
            assert len(item["name"]) >= 1

    def test_no_extra_fields_on_items(self, client: TestClient) -> None:
        items = client.get("/patterns/").json()["items"]
        for item in items:
            assert set(item.keys()) == {"name"}

    def test_names_match_catalog(self, client: TestClient) -> None:
        names = [p["name"] for p in client.get("/patterns/").json()["items"]]
        assert names == PATTERNS


# ---------------------------------------------------------------------------
# GET / (redirect to /patterns/)
# ---------------------------------------------------------------------------


class TestRootRedirect:
    def test_redirects_to_patterns(self, client: TestClient) -> None:
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 307
        assert resp.headers["location"] == "/patterns/"

    def test_following_redirect_returns_patterns(self, client: TestClient) -> None:
        resp = client.get("/", follow_redirects=True)
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()["items"]]
        assert names == PATTERNS
