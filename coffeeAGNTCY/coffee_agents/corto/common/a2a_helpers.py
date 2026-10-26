# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Small helpers for the protobuf types of a2a-sdk 1.x.

a2a-sdk 1.x responses carry their content in a ``payload`` oneof. This keeps
that detail in one place for the A2A clients in this project.
"""

from __future__ import annotations

from typing import Any

from a2a.types import Message


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
