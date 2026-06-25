# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for agents.supervisors.recruiter.models."""

import pytest
from a2a.types import AgentCard

from agents.supervisors.recruiter.models import (
    STATE_KEY_EVALUATION_RESULTS,
    STATE_KEY_RECRUITED_AGENTS,
    STATE_KEY_SELECTED_AGENT,
    STATE_KEY_TASK_MESSAGE,
    AgentProtocol,
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
            STATE_KEY_SELECTED_AGENT,
            STATE_KEY_TASK_MESSAGE,
        ):
            assert isinstance(key, str)

    def test_state_keys_are_unique(self):
        keys = [
            STATE_KEY_RECRUITED_AGENTS,
            STATE_KEY_EVALUATION_RESULTS,
            STATE_KEY_SELECTED_AGENT,
            STATE_KEY_TASK_MESSAGE,
        ]
        assert len(keys) == len(set(keys))


# ---------------------------------------------------------------------------
# AgentRecord
# ---------------------------------------------------------------------------


SAMPLE_CARD = {
    "name": "Test Agent",
    "description": "A test agent",
    "version": "2.0.0",
    "protocolVersion": "0.3.0",
    "url": "slim://slim:46357/lungo/agents/test",
    "preferredTransport": "slimrpc",
    "capabilities": {"streaming": True},
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
    "skills": [],
    "additionalInterfaces": [
        {"transport": "slimrpc", "url": "slim://slim:46357/lungo/agents/test"},
        {"transport": "jsonrpc", "url": "http://0.0.0.0:9999"},
    ],
}


class TestAgentRecord:
    def test_from_record_data_basics(self):
        record = AgentRecord.from_record_data("abc", SAMPLE_CARD)
        assert record.cid == "abc"
        assert record.name == "Test Agent"
        assert record.protocol == AgentProtocol.A2A
        assert isinstance(record.card, AgentCard)

    def test_from_record_data_preserves_transport_and_interfaces(self):
        """The full card is kept so the client factory can negotiate transport."""
        record = AgentRecord.from_record_data("abc", SAMPLE_CARD)
        assert record.card.preferred_transport == "slimrpc"
        assert record.card.additional_interfaces is not None
        assert {i.transport for i in record.card.additional_interfaces} == {
            "slimrpc",
            "jsonrpc",
        }

    def test_from_record_data_reads_protocol(self):
        record = AgentRecord.from_record_data("abc", {**SAMPLE_CARD, "protocol": "a2a"})
        assert record.protocol == AgentProtocol.A2A


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
