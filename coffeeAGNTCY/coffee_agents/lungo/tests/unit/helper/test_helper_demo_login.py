# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Grandma Helper's demo login: one built-in account guards the demo's routes."""

from __future__ import annotations

from fastapi.testclient import TestClient

from agents.supervisors.helper.main import DEMO_PASSWORD, DEMO_USERNAME, app


def _login(client: TestClient, password: str = DEMO_PASSWORD):
    return client.post("/login", json={"username": DEMO_USERNAME, "password": password})


def test_wrong_password_is_refused():
    client = TestClient(app)
    assert _login(client, "wrong").status_code == 401
    assert client.get("/me").status_code == 401


def test_routes_need_login():
    client = TestClient(app)
    assert client.post("/explain", json={"text": "hi"}).status_code == 401
    assert client.post("/reply", json={"text": "hi"}).status_code == 401
    assert client.get("/family/alerts").status_code == 401
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200


def test_login_then_logout():
    client = TestClient(app)
    res = client.post(
        "/login", json={"username": " Grandma ", "password": DEMO_PASSWORD}
    )
    assert res.status_code == 200
    assert client.get("/me").json() == {"username": DEMO_USERNAME}
    assert client.get("/family/alerts").status_code == 200

    client.post("/logout")
    assert client.get("/me").status_code == 401
