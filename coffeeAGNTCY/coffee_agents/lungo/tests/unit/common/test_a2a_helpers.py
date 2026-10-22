# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import pytest
from a2a.types import (
    AgentCard,
    AgentInterface,
    Artifact,
    Message,
    Part,
    Role,
    SendMessageResponse,
    StreamResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from agntcy_app_sdk.semantic.a2a.transport_types import InterfaceTransport

from common.a2a_helpers import (
    message_metadata,
    prefer_transport,
    primary_transport,
    response_message,
    response_text,
    task_state_label,
)


def _card() -> AgentCard:
    return AgentCard(
        name="Farm",
        supported_interfaces=[
            AgentInterface(
                protocol_binding=InterfaceTransport.SLIM_PATTERNS,
                url="slim://slim:46357/lungo/agents/farm",
            ),
            AgentInterface(
                protocol_binding=InterfaceTransport.NATS_PATTERNS,
                url="nats://nats:4222/lungo/agents/farm",
            ),
            AgentInterface(
                protocol_binding=InterfaceTransport.JSONRPC,
                url="http://0.0.0.0:9999",
            ),
        ],
    )


def _bindings(card: AgentCard) -> list[str]:
    return [i.protocol_binding for i in card.supported_interfaces]


def _agent_message(text: str, **metadata) -> Message:
    return Message(
        message_id="m1",
        role=Role.ROLE_AGENT,
        parts=[Part(text=text)],
        metadata=metadata or None,
    )


@pytest.mark.parametrize(
    "transport, first",
    [
        ("SLIM", "slimpatterns"),
        ("slim", "slimpatterns"),
        ("NATS", "natspatterns"),
        ("nats", "natspatterns"),
        ("jsonrpc", "jsonrpc"),
        ("JSONRPC", "jsonrpc"),
    ],
)
def test_prefer_transport_moves_match_first(transport, first):
    card = _card()
    preferred = prefer_transport(card, transport)
    assert _bindings(preferred)[0] == first
    assert sorted(_bindings(preferred)) == sorted(_bindings(card))


def test_prefer_transport_does_not_mutate_input():
    card = _card()
    before = _bindings(card)
    preferred = prefer_transport(card, "NATS")
    preferred.supported_interfaces[0].url = "changed"
    assert _bindings(card) == before
    assert all(i.url != "changed" for i in card.supported_interfaces)


def test_prefer_transport_without_match_keeps_order():
    card = _card()
    assert _bindings(prefer_transport(card, "carrier-pigeon")) == _bindings(card)
    assert _bindings(prefer_transport(card, "")) == _bindings(card)


@pytest.mark.parametrize(
    "transport, label",
    [
        ("SLIM", "slim"),
        ("NATS", "nats"),
        ("jsonrpc", "jsonrpc"),
    ],
)
def test_primary_transport_returns_ui_label(transport, label):
    assert primary_transport(prefer_transport(_card(), transport)) == label


def test_primary_transport_for_aliases_and_empty_cards():
    assert primary_transport(None) == ""
    assert primary_transport(AgentCard(name="x")) == ""
    slimrpc = AgentCard(
        name="x",
        supported_interfaces=[AgentInterface(protocol_binding="slimrpc", url="u")],
    )
    assert primary_transport(slimrpc) == "slimrpc"


def test_message_metadata():
    assert message_metadata(_agent_message("hi", name="Brazil")) == {"name": "Brazil"}
    assert message_metadata(_agent_message("hi")) == {}
    assert message_metadata(None) == {}


def test_response_message_and_text_for_send_message_response():
    message = _agent_message("hello", name="Brazil")
    resp = SendMessageResponse(message=message)
    assert response_message(resp) == message
    assert response_text(resp) == "hello"

    task = Task(id="t", context_id="c", status=TaskStatus(message=message))
    resp = SendMessageResponse(task=task)
    assert response_message(resp) == message
    assert response_text(resp) == "hello"


def test_task_without_status_message_falls_back_to_artifacts():
    task = Task(
        id="t",
        context_id="c",
        artifacts=[Artifact(artifact_id="a", parts=[Part(text="from artifact")])],
    )
    resp = SendMessageResponse(task=task)
    assert response_message(resp) is None
    assert response_text(resp) == "from artifact"


def test_response_message_and_text_for_stream_response():
    message = _agent_message("streamed")
    assert response_message(StreamResponse(message=message)) == message

    update = TaskStatusUpdateEvent(
        task_id="t", context_id="c", status=TaskStatus(message=message)
    )
    resp = StreamResponse(status_update=update)
    assert response_message(resp) == message
    assert response_text(resp) == "streamed"

    empty_update = StreamResponse(
        status_update=TaskStatusUpdateEvent(task_id="t", context_id="c")
    )
    assert response_message(empty_update) is None
    assert response_text(empty_update) == ""

    artifact = StreamResponse(
        artifact_update=TaskArtifactUpdateEvent(
            task_id="t",
            context_id="c",
            artifact=Artifact(artifact_id="a", parts=[Part(text="chunk")]),
        )
    )
    assert response_message(artifact) is None
    assert response_text(artifact) == "chunk"


def test_unset_payload_and_bare_message():
    assert response_message(StreamResponse()) is None
    assert response_text(StreamResponse()) == ""
    assert response_message(None) is None
    message = _agent_message("bare")
    assert response_message(message) is message
    assert response_text(message) == "bare"


@pytest.mark.parametrize(
    "state,expected",
    [
        (TaskState.TASK_STATE_SUBMITTED, "submitted"),
        (TaskState.TASK_STATE_WORKING, "working"),
        (TaskState.TASK_STATE_COMPLETED, "completed"),
        (TaskState.TASK_STATE_FAILED, "failed"),
        (TaskState.TASK_STATE_INPUT_REQUIRED, "input-required"),
        (TaskState.TASK_STATE_AUTH_REQUIRED, "auth-required"),
        (TaskState.TASK_STATE_UNSPECIFIED, "unknown"),
        (None, "unknown"),
    ],
)
def test_task_state_label_uses_v03_wire_names(state, expected):
    """Event status text keeps the a2a v0.3 lowercase, hyphenated labels."""
    assert task_state_label(state) == expected
