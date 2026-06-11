# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``POST /patterns/{name}/chat``.

Covers the pre-stream HTTP contract (404/422 paths) and the streaming
behaviour with the LLM stubbed at the ADK runner boundary so tests stay
fast and deterministic.
"""

from __future__ import annotations

import json
from typing import Any, NamedTuple
from unittest.mock import patch

import pytest
from api.agentic_workflows import pattern_chat
from api.agentic_workflows.router import create_agentic_workflows_router
from fastapi import FastAPI
from fastapi.testclient import TestClient
from google.adk.events.event import Event
from google.genai import types


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


@pytest.fixture(autouse=True)
def _isolate_pattern_chat_sessions():
    """Reset the module-level ADK session store before each test."""
    pattern_chat._session_service._sessions.clear() if hasattr(
        pattern_chat._session_service, "_sessions"
    ) else None
    yield


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


# ---------------------------------------------------------------------------
# Streaming behaviour (LLM stubbed at the ADK runner boundary)
# ---------------------------------------------------------------------------


def _text_event(text: str, *, partial: bool) -> Event:
    return Event(
        invocation_id="test",
        author="pattern_chat",
        content=types.Content(role="model", parts=[types.Part(text=text)]),
        partial=partial,
    )


def _function_call_event(name: str) -> Event:
    return Event(
        invocation_id="test",
        author="pattern_chat",
        content=types.Content(
            role="model",
            parts=[types.Part(function_call=types.FunctionCall(name=name, args={}))],
        ),
    )


def _function_response_event(name: str, payload: dict[str, Any]) -> Event:
    return Event(
        invocation_id="test",
        author="pattern_chat",
        content=types.Content(
            role="user",
            parts=[
                types.Part(
                    function_response=types.FunctionResponse(name=name, response=payload)
                )
            ],
        ),
    )


def _stub_runner_events(events: list[Event]):
    """Patch ``_runner.run_async`` to yield ``events`` regardless of arguments."""

    async def fake_run_async(*args, **kwargs):
        for ev in events:
            yield ev

    return patch.object(pattern_chat._runner, "run_async", side_effect=fake_run_async)


def _ndjson_lines(resp_iter) -> list[dict[str, Any]]:
    return [json.loads(line) for line in resp_iter if line]


def test_first_post_creates_session_and_seeds_markdown(client: TestClient) -> None:
    """Test 6 — first POST creates the ADK session and seeds the pattern markdown in state."""
    import asyncio

    events = [_text_event("hello", partial=False)]
    with _stub_runner_events(events):
        client.post(
            "/patterns/Feedback Loop/chat",
            json={"session_id": "sess-create-1", "message": "hi"},
        )

    session = asyncio.run(
        pattern_chat._session_service.get_session(
            app_name=pattern_chat.APP_NAME,
            user_id=pattern_chat.DEFAULT_USER_ID,
            session_id=pattern_chat._session_key("Feedback Loop", "sess-create-1"),
        )
    )
    assert session is not None, "session should be created on first POST"
    assert session.state.get(pattern_chat.STATE_KEY_PATTERN_NAME) == "Feedback Loop"
    markdown = session.state.get(pattern_chat.STATE_KEY_MARKDOWN, "")
    assert "```mermaid" in markdown, "session state must include the pattern markdown"


def test_second_post_reuses_session(client: TestClient) -> None:
    """Test 7 — second POST with the same session_id doesn't re-seed state."""
    import asyncio

    events = [_text_event("hello", partial=False)]
    with _stub_runner_events(events):
        client.post(
            "/patterns/Feedback Loop/chat",
            json={"session_id": "sess-reuse-1", "message": "first"},
        )

    sid = pattern_chat._session_key("Feedback Loop", "sess-reuse-1")
    first = asyncio.run(
        pattern_chat._session_service.get_session(
            app_name=pattern_chat.APP_NAME,
            user_id=pattern_chat.DEFAULT_USER_ID,
            session_id=sid,
        )
    )
    first_id = first.id

    with _stub_runner_events(events):
        client.post(
            "/patterns/Feedback Loop/chat",
            json={"session_id": "sess-reuse-1", "message": "second"},
        )

    second = asyncio.run(
        pattern_chat._session_service.get_session(
            app_name=pattern_chat.APP_NAME,
            user_id=pattern_chat.DEFAULT_USER_ID,
            session_id=sid,
        )
    )
    assert second.id == first_id, "second POST must reuse the existing ADK session"


def test_happy_path_streams_ndjson_then_done(client: TestClient) -> None:
    """Test 10 — partial chunks are forwarded as {"response": ...} and stream ends with {"done": true}."""
    events = [
        _text_event("Hel", partial=True),
        _text_event("lo ", partial=True),
        _text_event("world", partial=True),
        _text_event("Hello world", partial=False),  # final summary — must be suppressed
    ]
    with _stub_runner_events(events):
        with client.stream(
            "POST",
            "/patterns/Feedback Loop/chat",
            json={"session_id": "sess-happy-1", "message": "say hi"},
        ) as r:
            assert r.status_code == 200
            assert r.headers["content-type"].startswith("application/x-ndjson")
            lines = _ndjson_lines(r.iter_lines())

    assert lines == [
        {"response": "Hel"},
        {"response": "lo "},
        {"response": "world"},
        {"done": True},
    ]


def test_tool_call_events_are_filtered_from_stream(client: TestClient) -> None:
    """Test 12 — function_call / function_response events do not reach the FE stream."""
    events = [
        _function_call_event("read_pattern_doc"),
        _function_response_event("read_pattern_doc", {"result": "DOC"}),
        _text_event("Answer ", partial=True),
        _text_event("here.", partial=True),
    ]
    with _stub_runner_events(events):
        with client.stream(
            "POST",
            "/patterns/Feedback Loop/chat",
            json={"session_id": "sess-tool-1", "message": "explain"},
        ) as r:
            lines = _ndjson_lines(r.iter_lines())

    assert lines == [
        {"response": "Answer "},
        {"response": "here."},
        {"done": True},
    ]
