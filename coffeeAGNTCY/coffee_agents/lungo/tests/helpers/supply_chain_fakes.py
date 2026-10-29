# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Scriptable fake chat model for the Supply Chain Commitment unit tests."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage

Reply = str | BaseMessage | Callable[[list[BaseMessage]], BaseMessage | str]


class FakeLLM:
    """Pops one scripted reply per call and records every prompt it was given.

    A reply is text, a message (for example one with ``tool_calls``), a
    ``ConfirmDecision``-shaped value for structured calls, or a callable that
    receives the prompt.
    """

    def __init__(self, *replies: Reply):
        self.replies = list(replies)
        self.calls: list[list[BaseMessage]] = []
        self.bound_tools: list[Any] = []

    def __call__(self, **_kwargs: Any) -> FakeLLM:
        return self

    def bind_tools(self, tools: Any) -> FakeLLM:
        self.bound_tools.extend(tools)
        return self

    def with_structured_output(self, _schema: Any) -> FakeLLM:
        return self

    async def ainvoke(self, messages: list[BaseMessage]) -> Any:
        self.calls.append(list(messages))
        reply = self.replies.pop(0)
        if callable(reply):
            reply = reply(messages)
        return AIMessage(reply) if isinstance(reply, str) else reply

    def prompt_text(self, call: int = -1) -> str:
        return "\n".join(str(m.content) for m in self.calls[call])


class FakeGroupTransport:
    """In-memory stand-in for the SLIM group transport.

    It routes each step to real ``MemberAgent`` objects (so the addressing gate
    and reply shapes are the real ones) and records every call. The hooks let a
    test make the transport misbehave in the ways SLIM could.
    """

    def __init__(self, members: dict[str, Any]):
        self.members = members
        self.calls: list[tuple[Any, list[str]]] = []
        self.reverse = False
        self.drop: set[str] = set()
        self.duplicate: set[str] = set()
        self.error: Exception | None = None
        self.delay: float = 0.0
        self.transform: Callable[[Any], Any] | None = None

    async def broadcast(self, request, recipients, *, timeout):
        import asyncio

        self.calls.append((request, list(recipients)))
        if self.error is not None:
            raise self.error
        if self.delay:
            await asyncio.sleep(self.delay)
        replies = []
        for party in recipients:
            if party in self.drop:
                continue
            reply = await self.members[party].handle(request)
            if self.transform is not None:
                reply = self.transform(reply)
            replies.append(reply)
            if party in self.duplicate:
                replies.append(reply)
        return list(reversed(replies)) if self.reverse else replies
