# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Workflow context propagation across A2A, LangGraph, and OpenTelemetry.

Stores workflow_name and workflow_instance_id in OpenTelemetry baggage so
producers (LangGraph nodes, tools, and A2A callbacks) can emit events
without passing workflow identity through every function signature.

Use attach_workflow_context or workflow_context_scope to write values.
Use read_workflow_context to read a WorkflowContext value.

OpenTelemetry baggage is used because:
- It follows the OpenTelemetry context already propagated by ioa_observe.
- It is built on contextvars, so values are safe across await boundaries and
    isolated per asyncio task.
- It is represented as a W3C standard header, so it can cross A2A hops.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from opentelemetry import baggage as _otel_baggage
from opentelemetry import context as _otel_context
from opentelemetry.context import Token

logger = logging.getLogger("lungo.common.workflow_context_prop")

# Internal OpenTelemetry baggage keys. External code should use the public API.
_WORKFLOW_INSTANCE_ID_CONTEXT_KEY = "lungo.workflow_instance_id"
_WORKFLOW_NAME_CONTEXT_KEY = "lungo.workflow_name"


@dataclass(frozen=True)
class WorkflowContext:
    """Workflow identity stored on the current OpenTelemetry context.

    Values are independent of span validity. Callers can set context before
    any span exists, so reads may return values even when no trace is active.
    """

    instance_id: str | None = None
    workflow_name: str | None = None


def attach_workflow_context(
    *,
    workflow_instance_id: str | None,
    workflow_name: str | None,
) -> Token:
    """Attach workflow id and name to the current context.

    Returns a token that must be detached later.

    Call from a supervisor request handler when the caller provides a
    workflow_instance_id from the Agentic Workflows API. Pair with
    detach_workflow_context in a finally block, or use
    workflow_context_scope to handle attach/detach automatically.

    Raises ValueError when both values are None: the helper has no
    well-defined behavior in that case, and surfacing the bug at the
    call site is preferable to silently no-op'ing.
    """
    if not workflow_instance_id and not workflow_name:
        raise ValueError(
            "attach_workflow_context requires at least one of "
            "workflow_instance_id or workflow_name."
        )
    ctx = _otel_context.get_current()
    if workflow_instance_id:
        ctx = _otel_baggage.set_baggage(
            _WORKFLOW_INSTANCE_ID_CONTEXT_KEY, workflow_instance_id, context=ctx,
        )
    if workflow_name:
        ctx = _otel_baggage.set_baggage(
            _WORKFLOW_NAME_CONTEXT_KEY, workflow_name, context=ctx,
        )
    return _otel_context.attach(ctx)


def detach_workflow_context(token: Token | None) -> None:
    """Detach a token returned by attach_workflow_context.

    This is a no-op when token is None.
    """
    if token is not None:
        _otel_context.detach(token)


@contextmanager
def workflow_context_scope(
    *,
    workflow_instance_id: str | None = None,
    workflow_name: str | None = None,
) -> Iterator[None]:
    """Attach workflow context for the duration of a with block.

    This is a temporary shim for supervisor graph nodes that know workflow
    identity statically. Once every supervisor request carries workflow
    context from main.py, these per-node scopes become redundant and can
    be removed.
    """
    token = attach_workflow_context(
        workflow_instance_id=workflow_instance_id,
        workflow_name=workflow_name,
    )
    try:
        yield
    finally:
        detach_workflow_context(token)


def read_workflow_context() -> WorkflowContext:
    """Read workflow identity from the current OpenTelemetry context.

    Returns a WorkflowContext with both fields set to None when nothing has
    been propagated or values are not strings. Values may be present even
    before any span starts.
    """
    instance_id_val = _otel_baggage.get_baggage(_WORKFLOW_INSTANCE_ID_CONTEXT_KEY)
    workflow_name_val = _otel_baggage.get_baggage(_WORKFLOW_NAME_CONTEXT_KEY)
    return WorkflowContext(
        instance_id=instance_id_val if isinstance(instance_id_val, str) else None,
        workflow_name=workflow_name_val if isinstance(workflow_name_val, str) else None,
    )


__all__ = [
    "WorkflowContext",
    "attach_workflow_context",
    "detach_workflow_context",
    "read_workflow_context",
    "workflow_context_scope",
]
