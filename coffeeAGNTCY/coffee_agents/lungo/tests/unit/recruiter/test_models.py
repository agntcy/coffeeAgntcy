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
        """A legacy v0.3 card is converted with every interface kept, preferred first."""
        record = AgentRecord.from_record_data("abc", SAMPLE_CARD)
        interfaces = list(record.card.supported_interfaces)
        assert interfaces[0].protocol_binding == "slimrpc"
        assert interfaces[0].url == "slim://slim:46357/lungo/agents/test"
        assert {i.protocol_binding for i in interfaces} == {"slimrpc", "jsonrpc"}
        assert "http://0.0.0.0:9999" in {i.url for i in interfaces}

    def test_from_record_data_accepts_v1_card(self):
        """A card already in the a2a-sdk 1.x shape is parsed as is."""
        v1_card = {
            "name": "V1 Agent",
            "description": "desc",
            "version": "1.0.0",
            "supportedInterfaces": [
                {"protocolBinding": "JSONRPC", "url": "http://farm:9999"}
            ],
        }
        record = AgentRecord.from_record_data("abc", v1_card)
        [interface] = record.card.supported_interfaces
        assert interface.protocol_binding == "JSONRPC"
        assert interface.url == "http://farm:9999"

    def test_from_record_data_reads_protocol(self):
        record = AgentRecord.from_record_data("abc", {**SAMPLE_CARD, "protocol": "a2a"})
        assert record.protocol == AgentProtocol.A2A


# ---------------------------------------------------------------------------
# AgentRecord.from_record / OASF-aware to_agent_card
# ---------------------------------------------------------------------------


class TestAgentRecordFromRecord:
    @pytest.mark.parametrize(
        "case,record,expected_url,expected_transport",
        [
            (
                "oasf record extracts card_data url and transport",
                {
                    "name": "Accountant agent",
                    "modules": [
                        {
                            "name": "integration/a2a",
                            "data": {
                                "card_data": {
                                    "name": "Accountant agent",
                                    "url": "http://localhost:3000",
                                    "preferredTransport": "JSONRPC",
                                    "version": "1.0.0",
                                    "description": "An AI agent that confirms the payment.",
                                    "defaultInputModes": ["text"],
                                    "defaultOutputModes": ["text"],
                                    "capabilities": {"streaming": True},
                                    "skills": [],
                                    "supportsAuthenticatedExtendedCard": False,
                                }
                            },
                        }
                    ],
                },
                "http://localhost:3000",
                "JSONRPC",
            ),
            (
                "flat record fallback uses top-level url",
                {
                    "name": "Flat Agent",
                    "url": "http://farm:9999",
                    "preferredTransport": "slimrpc",
                    "description": "desc",
                    "version": "2.0.0",
                },
                "http://farm:9999",
                "slimrpc",
            ),
        ],
        ids=lambda case: case,
    )
    def test_to_agent_card_from_record(
        self, case, record, expected_url, expected_transport
    ):
        card = AgentRecord.from_record("cid-1", record).to_agent_card()

        assert isinstance(card, AgentCard)
        primary = card.supported_interfaces[0]
        assert primary.url == expected_url
        assert primary.protocol_binding == expected_transport

    def test_to_agent_card_returns_a_copy(self):
        record = AgentRecord.from_record("cid-1", {"name": "A", "url": "http://a:1"})
        card = record.to_agent_card()
        card.supported_interfaces[0].url = "http://changed:2"
        assert record.card.supported_interfaces[0].url == "http://a:1"

    @pytest.mark.parametrize(
        "case,record,expected_message",
        [
            (
                "missing name",
                {"description": "No name field"},
                "missing a name",
            ),
            (
                "empty name and no transport",
                {"name": "", "url": ""},
                "missing a name",
            ),
            (
                "name but no transport endpoint",
                {"name": "Orphan Agent", "description": "no url"},
                "no transport endpoint",
            ),
        ],
        ids=lambda case: case,
    )
    def test_from_record_rejects_unusable_card(self, case, record, expected_message):
        with pytest.raises(ValueError, match=expected_message):
            AgentRecord.from_record("cid-bad", record)


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
