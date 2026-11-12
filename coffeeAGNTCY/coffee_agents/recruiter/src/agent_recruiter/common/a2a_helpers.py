# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Small helpers for the protobuf types of a2a-sdk 1.x.

a2a-sdk 1.x types are protobuf messages: ``Message.metadata`` and
``Part.metadata`` are ``google.protobuf.Struct``, ``Part.data`` is a
``google.protobuf.Value``, a part carries its content in a ``content`` oneof,
and responses carry theirs in a ``payload`` oneof. These helpers keep those
details in one place for the recruiter server and the evaluator client.
"""

from __future__ import annotations

import json
from typing import Any

from a2a.types import Message, Part, Task
from google.protobuf import struct_pb2
from google.protobuf.json_format import MessageToDict, ParseDict


def _plain(value: Any) -> Any:
    """Turn the whole-number floats of a decoded ``Struct``/``Value`` back into ints.

    Protobuf stores every JSON number as a double, so ``MessageToDict`` returns
    ``3`` as ``3.0``. On the wire (JSON) it is still ``3``; this keeps it ``3``
    in Python too, so counts and ids round-trip unchanged.

    Applied only to data the recruiter receives (records, criteria, metadata),
    none of which declares float fields. A float that is a whole number
    (``1.0``) also comes back as ``1``, and integers beyond 2**53 are not exact,
    because ``Struct`` stores only doubles. The lungo client restores only
    ``id`` because its models declare float fields such as ``score``.
    """
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


def to_struct(data: dict[str, Any] | None) -> struct_pb2.Struct:
    """A ``Struct`` from a dict. Values that are not JSON types are stringified."""
    struct = struct_pb2.Struct()
    if data:
        ParseDict(json.loads(json.dumps(data, default=str)), struct)
    return struct


def text_part(text: str) -> Part:
    """A text ``Part``."""
    return Part(text=text)


def data_part(data: Any, metadata: dict[str, Any] | None = None) -> Part:
    """A data ``Part`` holding any JSON-compatible ``data``, with optional metadata."""
    part = Part(data=ParseDict(json.loads(json.dumps(data, default=str)), struct_pb2.Value()))
    if metadata:
        part.metadata.CopyFrom(to_struct(metadata))
    return part


def part_kind(part: Part) -> str | None:
    """``"text"``, ``"raw"``, ``"url"``, ``"data"`` or ``None`` for an empty part."""
    return part.WhichOneof("content")


def part_data(part: Part) -> Any:
    """The Python value of a data ``Part``."""
    return _plain(MessageToDict(part.data))


def part_metadata(part: Part) -> dict[str, Any]:
    """The metadata of a ``Part`` as a dict (empty when unset)."""
    return _plain(MessageToDict(part.metadata)) if part.HasField("metadata") else {}


def message_metadata(message: Message | None) -> dict[str, Any]:
    """The metadata of a ``Message`` as a dict (empty when unset)."""
    if message is None or not message.HasField("metadata"):
        return {}
    return _plain(MessageToDict(message.metadata))


def parts_text(parts: list[Part]) -> str:
    """Join the content of ``parts`` into one string.

    Text parts add their text, data parts their JSON, raw parts a size note
    and url parts their url.
    """
    text = ""
    for part in parts:
        kind = part_kind(part)
        if kind == "text":
            text += part.text
        elif kind == "data":
            text += json.dumps(part_data(part))
        elif kind == "url":
            text += part.url
        elif kind == "raw":
            text += f"<{len(part.raw)} bytes>"
    return text


def task_text(task: Task) -> str | None:
    """Text of a task: its artifacts, else its status message, else ``None``."""
    if not task.artifacts:
        if task.status.HasField("message") and task.status.message.parts:
            return parts_text(list(task.status.message.parts))
        return None

    text = ""
    for artifact in task.artifacts:
        if artifact.name:
            text += f"Artifact: {artifact.name}:\n"
        text += parts_text(list(artifact.parts))
        text += "\n"
    return text
