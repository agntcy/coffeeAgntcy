# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""JSON envelope carried in every Supply Chain Commitment A2A text part (D3).

The envelope is identified by its ``scc`` version key and its fields, never
by substrings, so agent-written ``body`` text cannot forge a control message.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

ENVELOPE_VERSION = 1
MODERATOR = "moderator"
RUN_END = "RUN_END"

Kind = Literal[
    "negotiation",
    "accord_request",
    "accord_reply",
    "concord_request",
    "concord_reply",
    "confirm_request",
    "confirm_reply",
    "event",
    "control",
    "noop",
]


class Envelope(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    scc: Literal[1] = ENVELOPE_VERSION
    run_id: str
    seq: int = Field(ge=0)
    sender: str = Field(alias="from")
    to: tuple[str, ...]
    kind: Kind
    phase: str = ""
    plan_version: int = Field(default=0, ge=0)
    reply_to: int | None = None
    case: str = ""
    configuration: str = ""
    body: str = ""
    transcript: tuple[dict[str, object], ...] = ()

    def encode(self) -> str:
        return json.dumps(self.model_dump(by_alias=True), ensure_ascii=False)

    def addressed_to(self, party: str) -> bool:
        return party in self.to and self.sender != party

    @property
    def is_run_end(self) -> bool:
        return self.kind == "control" and self.body == RUN_END


def decode(text: str) -> Envelope | None:
    """Return the envelope in ``text``, or ``None`` if it is not one."""
    try:
        raw = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(raw, dict) or raw.get("scc") != ENVELOPE_VERSION:
        return None
    try:
        return Envelope.model_validate(raw)
    except ValidationError:
        return None


def noop(request: Envelope, party: str) -> Envelope:
    return Envelope(
        run_id=request.run_id,
        seq=request.seq,
        sender=party,
        to=(request.sender,),
        kind="noop",
        reply_to=request.seq,
    )


def reply(request: Envelope, party: str, kind: Kind, body: str) -> Envelope:
    """Build a member's reply; the moderator assigns the reply its own ``seq``."""
    return Envelope(
        run_id=request.run_id,
        seq=request.seq,
        sender=party,
        to=(request.sender,),
        kind=kind,
        phase=request.phase,
        plan_version=request.plan_version,
        reply_to=request.seq,
        body=body,
    )
