# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
"""Integration tests for GET /agents/{slug}/oasf (static OASF files)."""
import pytest


REQUIRED_OASF_KEYS = {"name", "schema_version", "description"}


@pytest.mark.parametrize("slug", ["exchange-supervisor-agent", "flavor-profile-farm-agent"])
def test_get_agent_oasf_returns_200_and_valid_json(supervisor_client, slug):
    """GET /agents/{slug}/oasf returns 200 and valid OASF JSON from static files."""
    response = supervisor_client.get(f"/agents/{slug}/oasf")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    for key in REQUIRED_OASF_KEYS:
        assert key in data, f"OASF record must include '{key}'"
    assert data.get("name"), "OASF record must have non-empty name"


def test_get_agent_oasf_unknown_slug_returns_404(supervisor_client):
    """GET /agents/unknown-slug/oasf returns 404 when file does not exist."""
    response = supervisor_client.get("/agents/unknown-slug/oasf")
    assert response.status_code == 404
    assert "detail" in response.json()
