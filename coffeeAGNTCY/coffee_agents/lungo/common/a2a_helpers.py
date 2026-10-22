# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Small helpers for the protobuf types of a2a-sdk 1.x.

a2a-sdk 1.x types are protobuf messages: removed card fields cannot be
assigned, ``Message.metadata`` is a ``google.protobuf.Struct`` (not a dict),
and responses carry their content in a ``payload`` oneof. These helpers keep
those details in one place for every A2A client in this project.
"""

from __future__ import annotations

from typing import Any

from a2a.helpers import get_artifact_text, get_message_text
from a2a.types import AgentCard, AgentInterface, Message, TaskState
from agntcy_app_sdk.semantic.a2a.transport_types import normalize_transport
from google.protobuf.json_format import MessageToDict

# Canonical SDK transport name -> label the UI topology expects
# (frontend/src/utils/topologyToReactFlow.tsx TRANSPORT_SYNONYMS).
_UI_TRANSPORT_LABELS = {
    "slimpatterns": "slim",
    "natspatterns": "nats",
    "jsonrpc": "jsonrpc",
    "http": "jsonrpc",
    "slimrpc": "slimrpc",
}


def prefer_transport(card: AgentCard, transport: str) -> AgentCard:
    """Return a copy of ``card`` with the interface matching ``transport`` first.

    The SDK client negotiates in the order of ``supported_interfaces``, so
    moving an interface to the front selects it. Both the card binding and
    ``transport`` are normalized, so ``"SLIM"``, ``"slim"`` and
    ``"slimpatterns"`` all match. Without a match the copy keeps its order.
    The input card is never modified.
    """
    out = AgentCard()
    out.CopyFrom(card)
    wanted = normalize_transport(transport or "")
    interfaces = list(out.supported_interfaces)
    index = next(
        (
            i
            for i, iface in enumerate(interfaces)
            if normalize_transport(iface.protocol_binding) == wanted
        ),
        None,
    )
    if index is None or index == 0:
        return out
    ordered = [interfaces[index]] + interfaces[:index] + interfaces[index + 1 :]
    copies = []
    for iface in ordered:
        copy = AgentInterface()
        copy.CopyFrom(iface)
        copies.append(copy)
    del out.supported_interfaces[:]
    out.supported_interfaces.extend(copies)
    return out


def primary_transport(card: AgentCard | None) -> str:
    """UI label (``slim``/``nats``/``jsonrpc``/``slimrpc``) of the first interface."""
    if card is None or not card.supported_interfaces:
        return ""
    canonical = normalize_transport(card.supported_interfaces[0].protocol_binding)
    return _UI_TRANSPORT_LABELS.get(canonical, canonical)


def task_state_label(state: int | None) -> str:
    """v0.3-style label for a ``TaskState`` (``completed``, ``input-required``).

    ``TASK_STATE_UNSPECIFIED`` and ``None`` map to ``unknown``.
    """
    if not state:
        return "unknown"
    name = TaskState.Name(state)
    return name.removeprefix("TASK_STATE_").lower().replace("_", "-")


def message_metadata(message: Message | None) -> dict[str, Any]:
    """``message.metadata`` as a plain dict (empty when unset)."""
    if message is None or not message.HasField("metadata"):
        return {}
    return MessageToDict(message.metadata)


def response_message(response: Any) -> Message | None:
    """The ``Message`` carried by a ``SendMessageResponse`` or ``StreamResponse``.

    A bare ``Message`` is returned as is. For a task (or status update) the
    status message is returned when set. Artifact updates carry no message.
    """
    if response is None:
        return None
    if isinstance(response, Message):
        return response
    which = response.WhichOneof("payload")
    if which == "message":
        return response.message
    if which == "task":
        status = response.task.status
        return status.message if status.HasField("message") else None
    if which == "status_update":
        status = response.status_update.status
        return status.message if status.HasField("message") else None
    return None


def response_text(response: Any) -> str:
    """Text of a response: its message text, else the text of its artifacts."""
    if response is None:
        return ""
    message = response_message(response)
    if message is not None:
        text = get_message_text(message)
        if text:
            return text
    if isinstance(response, Message):
        return ""
    which = response.WhichOneof("payload")
    if which == "task":
        texts = [get_artifact_text(a) for a in response.task.artifacts]
        return "\n".join(t for t in texts if t)
    if which == "artifact_update":
        return get_artifact_text(response.artifact_update.artifact)
    return ""
