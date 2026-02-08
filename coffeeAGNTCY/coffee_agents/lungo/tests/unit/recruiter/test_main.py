# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.supervisors.recruiter.main (FastAPI endpoints)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from agents.supervisors.recruiter.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------


class TestHealthEndpoints:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_transport_config(self, client):
        resp = client.get("/transport/config")
        assert resp.status_code == 200
        assert resp.json()["transport"] == "A2A_HTTP"


# ---------------------------------------------------------------------------
# Agent card endpoint
# ---------------------------------------------------------------------------


class TestAgentCard:
    def test_agent_card_endpoint(self, client):
        resp = client.get("/.well-known/agent-card.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Recruiter Supervisor"
        assert "skills" in data

    def test_agent_card_has_capabilities(self, client):
        resp = client.get("/.well-known/agent-card.json")
        data = resp.json()
        assert "capabilities" in data
        assert data["capabilities"]["streaming"] is True


# ---------------------------------------------------------------------------
# Suggested prompts
# ---------------------------------------------------------------------------


class TestSuggestedPrompts:
    def test_suggested_prompts(self, client):
        resp = client.get("/suggested-prompts")
        assert resp.status_code == 200
        data = resp.json()
        assert "recruiter" in data
        assert len(data["recruiter"]) > 0


# ---------------------------------------------------------------------------
# POST /agent/prompt
# ---------------------------------------------------------------------------


class TestPromptEndpoint:
    def test_prompt_returns_response(self, client):
        with patch(
            "agents.supervisors.recruiter.main.call_agent",
            new_callable=AsyncMock,
            return_value={
                "response": "Here are the results",
                "session_id": "session-123",
                "agent_records": {"cid1": {"name": "Agent A"}},
                "evaluation_results": {},
            },
        ):
            resp = client.post(
                "/agent/prompt",
                json={"prompt": "Find me an accounting agent"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["response"] == "Here are the results"
            assert data["session_id"] == "session-123"
            assert "agent_records" in data
            assert data["agent_records"]["cid1"]["name"] == "Agent A"

    def test_prompt_with_session_id(self, client):
        with patch(
            "agents.supervisors.recruiter.main.call_agent",
            new_callable=AsyncMock,
            return_value={
                "response": "Response",
                "session_id": "my-session",
                "agent_records": {},
                "evaluation_results": {},
            },
        ) as mock_call:
            resp = client.post(
                "/agent/prompt",
                json={"prompt": "Test", "session_id": "my-session"},
            )
            assert resp.status_code == 200
            # Verify the session_id was passed through
            mock_call.assert_called_once_with(
                query="Test", session_id="my-session"
            )

    def test_prompt_generates_session_id_when_not_provided(self, client):
        with patch(
            "agents.supervisors.recruiter.main.call_agent",
            new_callable=AsyncMock,
            return_value={
                "response": "OK",
                "session_id": "auto-generated-id",
                "agent_records": {},
                "evaluation_results": {},
            },
        ):
            resp = client.post(
                "/agent/prompt",
                json={"prompt": "Test"},
            )
            data = resp.json()
            assert "session_id" in data
            assert data["session_id"] == "auto-generated-id"

    def test_prompt_error_returns_500(self, client):
        with patch(
            "agents.supervisors.recruiter.main.call_agent",
            new_callable=AsyncMock,
            side_effect=RuntimeError("LLM unavailable"),
        ):
            resp = client.post(
                "/agent/prompt",
                json={"prompt": "This will fail"},
            )
            assert resp.status_code == 500
            assert "LLM unavailable" in resp.json()["detail"]

    def test_prompt_returns_selected_agent(self, client):
        with patch(
            "agents.supervisors.recruiter.main.call_agent",
            new_callable=AsyncMock,
            return_value={
                "response": "Agent selected",
                "session_id": "session-123",
                "agent_records": {"cid1": {"name": "Shipping Agent"}},
                "evaluation_results": {},
                "selected_agent": {
                    "cid": "cid1",
                    "name": "Shipping Agent",
                    "description": "Ships things",
                },
            },
        ):
            resp = client.post(
                "/agent/prompt",
                json={"prompt": "Select Shipping Agent"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "selected_agent" in data
            assert data["selected_agent"]["name"] == "Shipping Agent"
            assert data["selected_agent"]["cid"] == "cid1"


# ---------------------------------------------------------------------------
# POST /agent/prompt/stream
# ---------------------------------------------------------------------------


class TestStreamEndpoint:
    def test_stream_returns_ndjson(self, client):
        async def fake_stream(query, session_id):
            event = MagicMock()
            event.is_final_response.return_value = True
            event.content = MagicMock()
            part = MagicMock()
            part.text = "Final answer"
            event.content.parts = [part]
            yield event, "stream-session"

        with patch(
            "agents.supervisors.recruiter.main.stream_agent",
            side_effect=fake_stream,
        ):
            resp = client.post(
                "/agent/prompt/stream",
                json={"prompt": "Find agents"},
            )
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("application/x-ndjson")

            lines = resp.text.strip().split("\n")
            assert len(lines) >= 1
            data = json.loads(lines[-1])
            assert data["response"]["event_type"] == "completed"
            assert data["response"]["message"] == "Final answer"

    def test_stream_intermediate_events(self, client):
        async def fake_stream(query, session_id):
            # Intermediate event
            event1 = MagicMock()
            event1.is_final_response.return_value = False
            event1.author = "recruiter_supervisor"
            event1.content = MagicMock()
            part1 = MagicMock()
            part1.text = "Searching..."
            event1.content.parts = [part1]
            yield event1, "s1"

            # Final event
            event2 = MagicMock()
            event2.is_final_response.return_value = True
            event2.content = MagicMock()
            part2 = MagicMock()
            part2.text = "Done"
            event2.content.parts = [part2]
            yield event2, "s1"

        with patch(
            "agents.supervisors.recruiter.main.stream_agent",
            side_effect=fake_stream,
        ):
            resp = client.post(
                "/agent/prompt/stream",
                json={"prompt": "Find agents"},
            )
            lines = resp.text.strip().split("\n")
            assert len(lines) == 2
            intermediate = json.loads(lines[0])
            assert intermediate["response"]["event_type"] == "status_update"
            assert intermediate["response"]["state"] == "working"

    def test_stream_with_session_id(self, client):
        async def fake_stream(query, session_id):
            event = MagicMock()
            event.is_final_response.return_value = True
            event.content = MagicMock()
            part = MagicMock()
            part.text = "OK"
            event.content.parts = [part]
            yield event, session_id

        with patch(
            "agents.supervisors.recruiter.main.stream_agent",
            side_effect=fake_stream,
        ):
            resp = client.post(
                "/agent/prompt/stream",
                json={"prompt": "Test", "session_id": "my-sess"},
            )
            lines = resp.text.strip().split("\n")
            data = json.loads(lines[0])
            assert data["session_id"] == "my-sess"


# ---------------------------------------------------------------------------
# OASF endpoint
# ---------------------------------------------------------------------------


class TestOasfEndpoint:
    def test_oasf_not_found(self, client):
        resp = client.get("/agents/nonexistent/oasf")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Deep health check (v1/health)
# ---------------------------------------------------------------------------


class TestDeepHealth:
    def test_v1_health_success(self, client):
        with patch("agents.supervisors.recruiter.main.httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            resp = client.get("/v1/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "alive"

    def test_v1_health_service_unreachable(self, client):
        import httpx

        with patch("agents.supervisors.recruiter.main.httpx.AsyncClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = httpx.ConnectError("Connection refused")
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_instance

            resp = client.get("/v1/health")
            assert resp.status_code == 502
