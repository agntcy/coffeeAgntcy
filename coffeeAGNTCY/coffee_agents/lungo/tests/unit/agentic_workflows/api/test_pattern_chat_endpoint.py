# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``POST /patterns/{name}/chat`` — pre-stream HTTP contract.

This file covers the request/response contract before any streaming is exercised:
unknown pattern → 404, missing markdown → 404, validation errors → 400.
Streaming behavior is exercised in a separate file (added in a later checkpoint).
"""

from __future__ import annotations

from typing import Any, NamedTuple

import pytest
from api.agentic_workflows.router import create_agentic_workflows_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


# Maximum permitted size of the ``message`` field. Mirrors the cap on
# ``PatternChatRequest.message`` in api.agentic_workflows.dtos so the boundary case
# below sends one byte too many.
_MAX_MESSAGE_BYTES = 32 * 1024


@pytest.fixture()
def client() -> TestClient:
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(create_agentic_workflows_router())
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Pre-stream HTTP contract
# ---------------------------------------------------------------------------


class Inputs(NamedTuple):
    pattern_name: str
    body: dict[str, Any] | None  # None → POST with no JSON body at all


class Outputs(NamedTuple):
    status: int
    detail_substr: str | None  # if set, response JSON ``detail`` must contain this


class Case(NamedTuple):
    case_id: str
    inputs: Inputs
    outputs: Outputs


_CASES: tuple[Case, ...] = (
    Case(
        case_id="unknown_pattern_returns_404",
        inputs=Inputs(
            pattern_name="Definitely Not A Pattern",
            body={"session_id": "00000000-0000-4000-a000-000000000001", "message": "hi"},
        ),
        outputs=Outputs(status=404, detail_substr="No reference material for pattern"),
    ),
    Case(
        # Pattern looks plausible but no markdown file exists for it.
        case_id="pattern_without_markdown_returns_404",
        inputs=Inputs(
            pattern_name="Some Pattern With No Doc File",
            body={"session_id": "00000000-0000-4000-a000-000000000002", "message": "hi"},
        ),
        outputs=Outputs(status=404, detail_substr="No reference material for pattern"),
    ),
    Case(
        case_id="empty_message_returns_400",
        inputs=Inputs(
            pattern_name="Feedback Loop",
            body={"session_id": "00000000-0000-4000-a000-000000000003", "message": ""},
        ),
        outputs=Outputs(status=422, detail_substr=None),  # pydantic validation = 422
    ),
    Case(
        case_id="missing_session_id_returns_422",
        inputs=Inputs(
            pattern_name="Feedback Loop",
            body={"message": "hi"},
        ),
        outputs=Outputs(status=422, detail_substr=None),
    ),
    Case(
        case_id="oversized_message_returns_400",
        inputs=Inputs(
            pattern_name="Feedback Loop",
            body={
                "session_id": "00000000-0000-4000-a000-000000000004",
                "message": "x" * (_MAX_MESSAGE_BYTES + 1),
            },
        ),
        outputs=Outputs(status=422, detail_substr=None),
    ),
)


@pytest.mark.parametrize("case", [pytest.param(c, id=c.case_id) for c in _CASES])
def test_pattern_chat_pre_stream(case: Case, client: TestClient) -> None:
    """All cases here fail before any streaming begins."""
    # URL-encode pattern name to handle spaces.
    url = f"/patterns/{case.inputs.pattern_name}/chat"
    if case.inputs.body is None:
        resp = client.post(url)
    else:
        resp = client.post(url, json=case.inputs.body)

    assert resp.status_code == case.outputs.status, (
        f"expected {case.outputs.status} for {case.case_id}, got {resp.status_code}: {resp.text}"
    )

    if case.outputs.detail_substr is not None:
        body = resp.json()
        assert "detail" in body, f"missing detail in {body}"
        assert case.outputs.detail_substr in body["detail"], (
            f"expected detail to contain {case.outputs.detail_substr!r}, got {body['detail']!r}"
        )
