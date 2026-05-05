# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Generated from ``schema/jsonschemas/event_type_v1.json``.

Do not edit by hand: regenerate with the ``jsonschema-to-pydantic-lungo`` skill.

Source description:
    Known business event types. Can be extended as needed for emitters. Listed
    values are validated by the event_v1 schema.
"""

from __future__ import annotations

from enum import StrEnum


class EventType(StrEnum):
    """Generated from ``$defs.event_type``.

    CURRENT VALUES ARE JUST PLACEHOLDERS. Need to be properly filled when
    implementing emitters.
    """

    RECRUITER_NODE_SEARCH = "RecruiterNodeSearch"
    STATE_PROGRESS_UPDATE = "StateProgressUpdate"
