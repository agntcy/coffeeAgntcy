# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Business event type enum (from ``event_type_v1.json`` ``$defs.event_type``)."""

from enum import StrEnum


class EventType(StrEnum):
    """Known emitter event types; extend when adding emitters."""

    RECRUITER_NODE_SEARCH = "RecruiterNodeSearch"
    STATE_PROGRESS_UPDATE = "StateProgressUpdate"
