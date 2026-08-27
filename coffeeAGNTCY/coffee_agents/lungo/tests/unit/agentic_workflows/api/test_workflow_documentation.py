# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from urllib.parse import quote

import pytest
from api.agentic_workflows.router import create_agentic_workflows_router
from api.agentic_workflows.workflow_documentation import (
    load_parsed_workflow_documentation,
    workflow_documentation_dir,
    workflow_name_to_documentation_slug,
)
from api.agentic_workflows.workflows import set_starting_workflows
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("name", "expected_slug"),
    [
        (
            "Publish Subscribe",
            "publish_subscribe",
        ),
        ("A2A HTTP", "a2a_http"),
        ("Event Ledger (Episodic Memory)", "event_ledger_episodic_memory"),
        ("Coordinator + Worker Agents", "coordinator_+_worker_agents"),
        ("Resilience & Re-Routing", "resilience_&_re-routing"),
        ("Sense-Decide-Act Loop", "sense-decide-act_loop"),
    ],
)
def test_workflow_name_to_documentation_slug(name: str, expected_slug: str) -> None:
    assert workflow_name_to_documentation_slug(name) == expected_slug


def test_load_parsed_real_file_has_pattern_section() -> None:
    parsed = load_parsed_workflow_documentation("publish_subscribe")
    assert parsed is not None
    headings = [h for _, h, _ in parsed.sections]
    assert "Pattern" in headings


def test_use_case_has_common_context_plus_unique_pattern_paragraph() -> None:
    seen: dict[str, str] = {}

    for path in sorted(workflow_documentation_dir().glob("*.md")):
        parsed = load_parsed_workflow_documentation(path.stem)
        assert parsed is not None, path.name

        pattern_body = next(
            (body for _, heading, body in parsed.sections if heading == "Pattern"),
            "",
        )
        is_stub = "> **TODO** - full pattern-level write-up." in pattern_body

        use_case_bodies = [
            body
            for _, heading, body in parsed.sections
            if heading == "Use case"
        ]

        if is_stub:
            assert not use_case_bodies, (
                f"{path.name}: explicit stub unexpectedly has a Use case section"
            )
            continue

        assert len(use_case_bodies) == 1, (
            f"{path.name}: expected exactly one Use case section"
        )

        body = re.sub(r"\n+---\s*$", "", use_case_bodies[0].strip())
        paragraphs = [
            paragraph.strip()
            for paragraph in re.split(r"\n\s*\n", body)
            if paragraph.strip()
        ]

        assert len(paragraphs) == 2, (
            f"{path.name}: expected common context plus one "
            "pattern-specific paragraph"
        )

        common, specific = paragraphs
        assert common.startswith(
            "**Coffee Agntcy** is a coffee company"
        ), path.name

        specific = " ".join(specific.split())
        assert specific, f"{path.name}: empty pattern-specific paragraph"
        assert specific not in seen, (
            f"{path.name} duplicates {seen[specific]}"
        )
        seen[specific] = path.name

    assert seen


@pytest.fixture()
def doc_client(workflow_api_headers: dict[str, str]) -> TestClient:
    set_starting_workflows()
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    return TestClient(app, headers=workflow_api_headers)


def test_get_workflow_documentation_200(doc_client: TestClient) -> None:
    name = "Publish Subscribe"
    r = doc_client.get(
        f"/agentic-workflows/{quote(name, safe='')}/documentation/",
    )
    assert r.status_code == 200
    data = r.json()
    assert data["workflow_name"] == name
    assert data["slug"] == "publish_subscribe"
    assert data["pattern_category"] == "Orchestration & Control Flow"
    assert any(s["heading"] == "Pattern" for s in data["sections"])
    assert len(data["full_markdown"]) > 0


def test_get_workflow_documentation_unknown_workflow(doc_client: TestClient) -> None:
    r = doc_client.get(
        "/agentic-workflows/NoSuchWorkflowName/documentation/",
    )
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()
