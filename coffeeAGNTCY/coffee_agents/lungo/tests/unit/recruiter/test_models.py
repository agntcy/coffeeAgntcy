# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.supervisors.recruiter.models."""

import pytest
from a2a.types import AgentCard

from agents.supervisors.recruiter.models import (
    STATE_KEY_EVALUATION_RESULTS,
    STATE_KEY_RECRUITED_AGENTS,
    STATE_KEY_SELECTED_AGENT_CIDS,
    STATE_KEY_TASK_MESSAGE,
    AgentRecord,
    RecruitmentResponse,
)


# ---------------------------------------------------------------------------
# State key constants
# ---------------------------------------------------------------------------


class TestStateKeys:
    def test_state_keys_are_strings(self):
        for key in (
            STATE_KEY_RECRUITED_AGENTS,
            STATE_KEY_EVALUATION_RESULTS,
            STATE_KEY_SELECTED_AGENT_CIDS,
            STATE_KEY_TASK_MESSAGE,
        ):
            assert isinstance(key, str)

    def test_state_keys_are_unique(self):
        keys = [
            STATE_KEY_RECRUITED_AGENTS,
            STATE_KEY_EVALUATION_RESULTS,
            STATE_KEY_SELECTED_AGENT_CIDS,
            STATE_KEY_TASK_MESSAGE,
        ]
        assert len(keys) == len(set(keys))


# ---------------------------------------------------------------------------
# AgentRecord
# ---------------------------------------------------------------------------


class TestAgentRecord:
    def test_minimal_construction(self):
        record = AgentRecord(cid="abc", name="Test", url="http://localhost:9000")
        assert record.cid == "abc"
        assert record.name == "Test"
        assert record.url == "http://localhost:9000"
        assert record.description == ""

    def test_full_construction(self):
        record = AgentRecord(
            cid="abc",
            name="Test Agent",
            description="A test agent",
            url="http://localhost:9000",
            version="2.0.0",
            skills=[{"id": "s1", "name": "Skill 1"}],
        )
        assert record.version == "2.0.0"
        assert len(record.skills) == 1

    def test_to_agent_card_returns_valid_card(self):
        record = AgentRecord(
            cid="abc",
            name="Test Agent",
            description="A test",
            url="http://localhost:9000",
            version="2.0.0",
        )
        card = record.to_agent_card()

        assert isinstance(card, AgentCard)
        assert card.name == "Test Agent"
        assert card.url == "http://localhost:9000"
        assert card.description == "A test"
        assert card.version == "2.0.0"

    def test_to_safe_agent_name_simple(self):
        record = AgentRecord(cid="x", name="my_agent", url="http://x")
        assert record.to_safe_agent_name() == "my_agent"

    def test_to_safe_agent_name_with_spaces_and_special_chars(self):
        record = AgentRecord(cid="x", name="My Agent (v2)", url="http://x")
        safe = record.to_safe_agent_name()
        assert safe.isidentifier(), f"'{safe}' is not a valid identifier"
        assert "my" in safe.lower()

    def test_to_safe_agent_name_starting_with_number(self):
        record = AgentRecord(cid="x", name="123-agent", url="http://x")
        safe = record.to_safe_agent_name()
        assert safe.isidentifier(), f"'{safe}' is not a valid identifier"
        assert safe.startswith("agent_")

    def test_to_safe_agent_name_with_hyphens(self):
        record = AgentRecord(cid="x", name="accounting-agent-v3", url="http://x")
        safe = record.to_safe_agent_name()
        assert safe.isidentifier(), f"'{safe}' is not a valid identifier"

    def test_to_safe_agent_name_empty_name(self):
        """Edge case: if name somehow becomes empty after sanitisation."""
        record = AgentRecord(cid="x", name="---", url="http://x")
        safe = record.to_safe_agent_name()
        assert safe.isidentifier(), f"'{safe}' is not a valid identifier"


# ---------------------------------------------------------------------------
# RecruitmentResponse
# ---------------------------------------------------------------------------


class TestRecruitmentResponse:
    def test_defaults(self):
        resp = RecruitmentResponse()
        assert resp.text is None
        assert resp.agent_records == {}
        assert resp.evaluation_results == {}

    def test_with_data(self):
        resp = RecruitmentResponse(
            text="Found 2 agents",
            agent_records={"cid1": {"name": "A"}, "cid2": {"name": "B"}},
            evaluation_results={"cid1": {"score": 0.9}},
        )
        assert resp.text == "Found 2 agents"
        assert len(resp.agent_records) == 2
        assert resp.evaluation_results["cid1"]["score"] == 0.9
