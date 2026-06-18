# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for OASF annotation → topology UI enrichment."""

from __future__ import annotations

import logging
from typing import NamedTuple

import pytest
from api.agentic_workflows.agent_ui_enrichment import (
    clear_agent_ui_cache,
    enrich_topology_dict,
    register_from_record,
)
from common.stable_agent_id import stable_agent_uuid_for_name


class EnrichCase(NamedTuple):
    case_id: str
    record: dict
    agent_name: str
    expected_keys: set[str]
    expected_agent_directory_cid: str | None


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_agent_ui_cache()
    yield
    clear_agent_ui_cache()


_ENRICH_CASES: tuple[EnrichCase, ...] = (
    EnrichCase(
        case_id="brazil_overrides",
        agent_name="Brazil Coffee Farm",
        record={
            "name": "Brazil Coffee Farm",
            "annotations": {
                "lungo.agentDirectoryCid": "/cid-brazil",
                "lungo.hasBadgeOverride": "false",
                "lungo.hasPolicyOverride": "false",
                "lungo.verificationStatusOverride": "failed",
            },
        },
        expected_keys={
            "agent_directory_cid",
            "has_badge_override",
            "has_policy_override",
            "verification_status_override",
        },
        expected_agent_directory_cid="/cid-brazil",
    ),
    EnrichCase(
        case_id="auction_identity_only",
        agent_name="Auction Supervisor agent",
        record={
            "name": "Auction Supervisor agent",
            "annotations": {
                "lungo.agentDirectoryCid": "/cid-auction",
                "lungo.identityAppSlug": "auction-supervisor",
            },
        },
        expected_keys={"agent_directory_cid", "identity_app_slug"},
        expected_agent_directory_cid="/cid-auction",
    ),
)


@pytest.mark.parametrize("case", [pytest.param(c, id=c.case_id) for c in _ENRICH_CASES])
def test_enrich_topology_dict_from_annotations(case: EnrichCase) -> None:
    stable_uuid = str(stable_agent_uuid_for_name(case.agent_name))
    register_from_record(stable_uuid, case.record)
    topology = enrich_topology_dict(
        {
            "nodes": [
                {
                    "id": "node://00000000-0000-4000-a000-000000000001",
                    "stable_agent_id": f"agent://{stable_uuid}",
                    "type": "customNode",
                    "label": "Test",
                },
            ],
            "edges": [],
        },
    )
    node = topology["nodes"][0]
    assert case.expected_keys.issubset(set(node.keys()))
    assert node.get("agent_directory_cid") == case.expected_agent_directory_cid
    if "has_badge_override" in case.expected_keys:
        assert node["has_badge_override"] is False


def test_register_from_record_logs_invalid_bool_override(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    register_from_record(
        "00000000-0000-4000-a000-000000000099",
        {
            "name": "Misconfigured Agent",
            "annotations": {
                "lungo.hasBadgeOverride": "not-a-bool",
                "lungo.hasPolicyOverride": "maybe",
            },
        },
    )
    assert any(
        "Invalid lungo.hasBadgeOverride" in record.message for record in caplog.records
    )
    assert any(
        "Invalid lungo.hasPolicyOverride" in record.message for record in caplog.records
    )
