# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the recruiter A2A server (a2a-sdk 1.x) with a stubbed agent team.

The app is exercised in process through an ASGI transport, with both a 1.x
client. The server speaks A2A v1.0 only (v0.3 compat is off).
"""

from uuid import uuid4

import httpx
import pytest
from a2a.client import ClientConfig, ClientFactory
from a2a.types import (
    AgentInterface,
    Message,
    Role,
    SendMessageRequest,
    TaskState,
)
from google.adk.events.event import Event as AdkEvent
from google.genai import types as genai_types

import agent_recruiter.server.agent_executor as executor_module
from agent_recruiter.common.a2a_helpers import (
    data_part,
    message_metadata,
    part_data,
    part_kind,
    part_metadata,
    text_part,
)
from agent_recruiter.server.app import build_app
from agent_recruiter.server.card import AGENT_CARD

FOUND_RECORDS = {"cid-1": {"name": "Accountant agent"}}
EVALUATION_RESULTS = {"_summary": {"status": "done"}}


class FakeTeam:
    """Stands in for ``RecruiterTeam``: no LLM, one final ADK event."""

    last_overrides: dict | None = None

    async def stream(self, prompt, user_id, session_id, initial_state_overrides=None):
        FakeTeam.last_overrides = initial_state_overrides
        FakeTeam.last_user_id = user_id
        yield AdkEvent(
            author="recruiter",
            content=genai_types.Content(
                role="model", parts=[genai_types.Part(text=f"found for: {prompt}")]
            ),
        )

    async def get_found_agent_records(self, user_id, session_id):
        return FOUND_RECORDS

    async def get_evaluation_results(self, user_id, session_id):
        return EVALUATION_RESULTS


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(executor_module, "RecruiterTeam", FakeTeam)
    FakeTeam.last_overrides = None
    return build_app(AGENT_CARD, executor_module.RecruiterAgentExecutor())


def _card_for(protocol_version: str):
    """The recruiter card pointed at the in-process app, with the given interface version."""
    card = type(AGENT_CARD)()
    card.CopyFrom(AGENT_CARD)
    del card.supported_interfaces[:]
    card.supported_interfaces.append(
        AgentInterface(
            protocol_binding="JSONRPC",
            url="http://recruiter.test/",
            protocol_version=protocol_version,
        )
    )
    return card


async def _send(app, protocol_version: str, message: Message, streaming: bool):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, timeout=30) as http:
        client = ClientFactory(
            ClientConfig(httpx_client=http, streaming=streaming)
        ).create(_card_for(protocol_version))
        return [
            event
            async for event in client.send_message(SendMessageRequest(message=message))
        ]


def _user_message(*parts) -> Message:
    return Message(role=Role.ROLE_USER, message_id=str(uuid4()), parts=list(parts))


def _completed_message(events) -> Message:
    """The status message of the last completed status update or task."""
    for event in reversed(events):
        which = event.WhichOneof("payload")
        if which == "status_update":
            status = event.status_update.status
        elif which == "task":
            status = event.task.status
        else:
            continue
        if status.state == TaskState.TASK_STATE_COMPLETED:
            return status.message
    raise AssertionError("no completed status in " + repr(events))


@pytest.mark.parametrize(
    "path", ["/.well-known/agent-card.json", "/.well-known/agent.json"]
)
async def test_agent_card_is_served_at_both_well_known_paths(app, path):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://recruiter.test"
    ) as http:
        response = await http.get(path)

    assert response.status_code == 200
    card = response.json()
    assert card["name"] == "RecruiterAgent"
    assert card["capabilities"]["streaming"] is True
    assert card["supportedInterfaces"][0]["protocolBinding"] == "JSONRPC"


@pytest.mark.parametrize(
    "path", ["/.well-known/agent-card.json", "/.well-known/agent.json"]
)
async def test_agent_card_has_no_v03_only_fields(app, path):
    """The card is A2A v1.0 only: no url, protocolVersion or preferredTransport."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://recruiter.test"
    ) as http:
        card = (await http.get(path)).json()

    assert {"url", "protocolVersion", "preferredTransport"}.isdisjoint(card)


def test_card_declares_only_the_1_0_interface():
    versions = [i.protocol_version for i in AGENT_CARD.supported_interfaces]
    assert versions == ["1.0"]


async def test_a_v03_request_is_not_served(app):
    """v0.3 compat is off: ``message/send`` is not a v1.0 method."""
    body = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "message/send",
        "params": {
            "message": {
                "kind": "message",
                "messageId": "m-1",
                "role": "user",
                "parts": [{"kind": "text", "text": "hi"}],
            }
        },
    }
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://recruiter.test"
    ) as http:
        response = await http.post("/", json=body)

    assert response.json().get("error", {}).get("code") == -32601
    assert FakeTeam.last_overrides is None


@pytest.mark.parametrize("streaming", [True, False])
async def test_message_returns_text_and_data_parts(app, streaming):
    message = _user_message(text_part("find an accountant"))

    events = await _send(app, "1.0", message, streaming)

    final = _completed_message(events)
    assert message_metadata(final)["name"] == "RecruiterAgent"
    by_kind = {}
    for part in final.parts:
        key = part_metadata(part).get("type", part_kind(part))
        by_kind[key] = part_data(part) if part_kind(part) == "data" else part.text
    assert by_kind["text"] == "found for: find an accountant"
    assert by_kind["found_agent_records"] == FOUND_RECORDS
    assert by_kind["evaluation_results"] == EVALUATION_RESULTS


async def test_streaming_emits_working_updates_before_the_terminal_one(app):
    events = await _send(app, "1.0", _user_message(text_part("hi")), streaming=True)

    updates = [
        e.status_update for e in events if e.WhichOneof("payload") == "status_update"
    ]
    assert [u.status.state for u in updates][0] == TaskState.TASK_STATE_WORKING
    assert updates[-1].status.state == TaskState.TASK_STATE_COMPLETED
    first = updates[0].status.message
    assert message_metadata(first)["event_type"] == "processing_started"


async def test_data_parts_of_the_request_seed_the_session_state(app):
    message = _user_message(
        text_part("evaluate these"),
        data_part(FOUND_RECORDS, metadata={"type": "found_agent_records"}),
        data_part(
            [{"scenario": "be polite"}], metadata={"type": "evaluation_criteria"}
        ),
    )

    await _send(app, "1.0", message, streaming=True)

    assert FakeTeam.last_overrides == {
        "found_agent_records": FOUND_RECORDS,
        "evaluation_criteria": [{"scenario": "be polite"}],
    }


async def test_user_id_comes_from_the_message_metadata(app):
    message = _user_message(text_part("hi"))
    message.metadata.update({"user_id": "alice"})

    await _send(app, "1.0", message, streaming=True)

    assert FakeTeam.last_user_id == "alice"


def test_card_advertises_a_dialable_url_by_default():
    urls = {i.url for i in AGENT_CARD.supported_interfaces}
    assert urls == {"http://localhost:8881"}


def test_an_empty_recruiter_agent_url_falls_back_to_the_default(monkeypatch):
    import importlib

    import agent_recruiter.server.card as card_module

    monkeypatch.setenv("RECRUITER_AGENT_URL", "")
    try:
        reloaded = importlib.reload(card_module)
        url = reloaded.RECRUITER_AGENT_URL
    finally:
        monkeypatch.undo()
        importlib.reload(card_module)

    assert url == "http://localhost:8881"


@pytest.mark.parametrize(
    "url", ["http://0.0.0.0:8881", "http://[::]:8881", "http://:8881", "8881"]
)
def test_a_wildcard_advertised_url_is_rejected(url):
    from agent_recruiter.server.card import check_advertised_url

    with pytest.raises(ValueError, match="not an address clients can dial"):
        check_advertised_url(url)


@pytest.mark.parametrize("in_container", [True, False])
def test_a_loopback_url_is_flagged_only_inside_a_container(monkeypatch, in_container):
    import agent_recruiter.server.card as card_module

    monkeypatch.setattr(card_module, "_in_container", lambda: in_container)

    warning = card_module.check_advertised_url("http://localhost:8881")

    assert (warning is not None) is in_container


def test_a_resolvable_url_passes_the_check(monkeypatch):
    import agent_recruiter.server.card as card_module

    monkeypatch.setattr(card_module, "_in_container", lambda: True)

    assert card_module.check_advertised_url("http://recruiter:8881") is None


def test_card_url_comes_from_recruiter_agent_url(monkeypatch):
    import importlib

    import agent_recruiter.server.card as card_module

    monkeypatch.setenv("RECRUITER_AGENT_URL", "http://recruiter:8881")
    try:
        reloaded = importlib.reload(card_module)
        urls = {i.url for i in reloaded.AGENT_CARD.supported_interfaces}
    finally:
        monkeypatch.undo()
        importlib.reload(card_module)

    assert urls == {"http://recruiter:8881"}


def test_server_bind_address_is_independent_of_the_card_url(monkeypatch):
    from agent_recruiter.server.server import _bind_address

    monkeypatch.delenv("RECRUITER_BIND_HOST", raising=False)
    monkeypatch.delenv("RECRUITER_PORT", raising=False)
    assert _bind_address() == ("0.0.0.0", 8881)

    monkeypatch.setenv("RECRUITER_BIND_HOST", "127.0.0.1")
    monkeypatch.setenv("RECRUITER_PORT", "9000")
    assert _bind_address() == ("127.0.0.1", 9000)
