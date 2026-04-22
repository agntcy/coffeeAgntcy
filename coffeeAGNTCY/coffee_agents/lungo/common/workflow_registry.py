# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Workflow catalog, tool registration, and resolution helpers.

This module centralizes how tools map to workflow catalog entries from
``api/agentic_workflows/starting_workflows.json``.

Main entry points:

- ``@register_workflow(workflow_name)`` to bind tools to catalog workflows.
- ``workflow_names()`` to access generated workflow-name constants.
- ``make_tool_call_context(...)`` to build a consistent ``"tool"`` context.
- ``get_workflow_registry()`` to access the shared, validated registry.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from a2a.client.middleware import ClientCallContext

from common.a2a_event_middleware import WorkflowIdentity

logger = logging.getLogger("lungo.common.workflow_registry")


# ---------------------------------------------------------------------------
# Catalog source
# ---------------------------------------------------------------------------
# The catalog is read directly from starting_workflows.json so this module has
# no runtime dependency on api.agentic_workflows (which may not be importable
# from every entrypoint — e.g. tool-only consumers, tests, scripts run from a
# different CWD, or environments where another 'api' namespace shadows the
# local package). The JSON is the single source of truth; only the three
# identity fields (name, pattern, use_case) are consumed here.
_DEFAULT_WORKFLOWS_JSON = (
    Path(__file__).resolve().parents[1]
    / "api" / "agentic_workflows" / "starting_workflows.json"
)


def _workflows_json_path() -> Path:
    """Return the path to starting_workflows.json, honouring the env override."""
    override = os.getenv("LUNGO_WORKFLOWS_JSON")
    return Path(override) if override else _DEFAULT_WORKFLOWS_JSON


# ---------------------------------------------------------------------------
# Tool identity
# ---------------------------------------------------------------------------

def _tool_identity_key(obj: Any) -> str:
    """Return a stable string key for a tool object.

    Probes ``StructuredTool.name`` → ``__name__`` → ``__wrapped__.__name__``
    so the same key is used whether the caller passes a plain async
    function, a ``@tool``-wrapped ``StructuredTool``, or anything
    ``functools.wraps``-wrapped.
    """
    key = (
        getattr(obj, "name", None)
        or getattr(obj, "__name__", None)
        or getattr(getattr(obj, "__wrapped__", None), "__name__", None)
    )
    if not isinstance(key, str) or not key:
        raise TypeError(f"Cannot derive tool identity key from {obj!r}")
    return key


# ---------------------------------------------------------------------------
# Generated WorkflowNames constants
# ---------------------------------------------------------------------------

def _slugify_const(name: str) -> str:
    """Workflow name → Python-safe uppercase identifier."""
    s = re.sub(r"[^0-9A-Za-z]+", "_", name).strip("_").upper()
    if not s:
        return "WF_UNKNOWN"
    if s[0].isdigit():
        s = "WF_" + s
    return s


def _build_workflow_names(catalog: dict[str, WorkflowIdentity]) -> SimpleNamespace:
    """Build a ``SimpleNamespace`` of uppercase-slug → workflow name."""
    ns: dict[str, str] = {}
    for wf_name in catalog:
        const = _slugify_const(wf_name)
        if const in ns and ns[const] != wf_name:
            raise ValueError(
                f"Workflow name collision: {wf_name!r} and {ns[const]!r} "
                f"both slugify to {const!r}"
            )
        ns[const] = wf_name
    return SimpleNamespace(**ns)


# Populated by get_workflow_registry() on first call.
WorkflowNames: SimpleNamespace = SimpleNamespace()


def workflow_names() -> SimpleNamespace:
    """Return the generated ``WorkflowNames`` namespace.

    Hydrates the catalog if it has not been loaded yet. Prefer this over
    importing :data:`WorkflowNames` directly so call sites always see the
    populated namespace regardless of module-import order.
    """
    get_workflow_registry()
    return WorkflowNames


# ---------------------------------------------------------------------------
# Registration state
# ---------------------------------------------------------------------------

_TOOL_WORKFLOW_MAP: dict[str, str] = {}


def register_workflow(workflow_name: str):
    """Decorator that registers a tool against a catalog workflow name.

    Validates *workflow_name* against the catalog eagerly so typos — or
    any fallback to a raw string — fail at import time rather than at
    first tool call. The decorator is a pass-through: it does not wrap
    or replace the decorated object, so stacked decorators such as
    ``@tool`` and ``@ioa_tool_decorator`` behave identically to an
    unregistered tool.
    """
    # Eager validation against the catalog — raises KeyError on typo.
    get_workflow_registry().get(workflow_name)

    def decorator(obj):
        key = _tool_identity_key(obj)
        existing = _TOOL_WORKFLOW_MAP.get(key)
        if existing is not None and existing != workflow_name:
            raise ValueError(
                f"Tool {key!r} already registered to workflow {existing!r}; "
                f"cannot re-register to {workflow_name!r}"
            )
        _TOOL_WORKFLOW_MAP[key] = workflow_name
        return obj

    return decorator


def make_tool_call_context(tool_obj: Any, **extra: Any) -> ClientCallContext:
    """Build a ``ClientCallContext`` whose ``"tool"`` state matches registration.

    Use this at every A2A call site instead of constructing
    ``ClientCallContext`` inline so the registration key and the lookup
    key share one derivation path.
    """
    return ClientCallContext(state={"tool": _tool_identity_key(tool_obj), **extra})


# ---------------------------------------------------------------------------
# Registration / resolution primitives
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorkflowRegistration:
    """Per-supervisor registration of tool-specific workflows.

    ``default_workflow_name`` is optional. Supervisors may register every
    tool explicitly when they can initiate several unrelated workflows.
    """

    tool_workflow_map: dict[str, str] = field(default_factory=dict)
    default_workflow_name: str | None = None


class WorkflowRegistry:
    """Lookup validated workflow metadata by workflow name."""

    def __init__(self, workflows_by_name: dict[str, WorkflowIdentity]) -> None:
        if not workflows_by_name:
            raise ValueError("workflows_by_name must not be empty")
        self._workflows_by_name = dict(workflows_by_name)

    def get(self, workflow_name: str) -> WorkflowIdentity:
        """Return workflow metadata for *workflow_name* or raise."""
        try:
            return self._workflows_by_name[workflow_name]
        except KeyError as exc:
            raise KeyError(f"Unknown workflow name: {workflow_name}") from exc

    def validate_registration(self, registration: WorkflowRegistration) -> None:
        """Ensure every registered workflow name exists in the catalog."""
        if not registration.tool_workflow_map and registration.default_workflow_name is None:
            raise ValueError(
                "WorkflowRegistration must declare at least one tool workflow "
                "or a default_workflow_name"
            )
        if registration.default_workflow_name is not None:
            self.get(registration.default_workflow_name)
        for workflow_name in registration.tool_workflow_map.values():
            self.get(workflow_name)


class ToolWorkflowResolver:
    """Resolve tool names to catalog workflow metadata."""

    def __init__(
        self,
        *,
        registry: WorkflowRegistry,
        registration: WorkflowRegistration,
    ) -> None:
        registry.validate_registration(registration)
        self._registry = registry
        self._registration = registration

    def resolve(self, tool_name: str | None) -> WorkflowIdentity:
        """Resolve the workflow for *tool_name*.

        Exact tool registration wins. Unknown tools only fall back when an
        explicit supervisor default is configured.
        """
        if tool_name and tool_name in self._registration.tool_workflow_map:
            return self._registry.get(self._registration.tool_workflow_map[tool_name])

        if self._registration.default_workflow_name is not None:
            if tool_name:
                logger.warning(
                    "ToolWorkflowResolver: tool %r not explicitly registered; "
                    "falling back to %r",
                    tool_name,
                    self._registration.default_workflow_name,
                )
            return self._registry.get(self._registration.default_workflow_name)

        if tool_name is None:
            raise KeyError("No default workflow registered for standalone resolution")
        raise KeyError(f"No workflow registered for tool: {tool_name}")


def build_registration_from_decorators(
    *, default_workflow_name: str | None = None,
) -> WorkflowRegistration:
    """Snapshot the decorator-collected tool map into a ``WorkflowRegistration``.

    Call after all tool modules have been imported. Raises
    :class:`RuntimeError` if the map is empty, catching refactors that
    accidentally build the resolver before the tools are defined.
    """
    if not _TOOL_WORKFLOW_MAP:
        raise RuntimeError(
            "No tools registered via @register_workflow. "
            "Ensure the tool module is imported before building the resolver."
        )
    return WorkflowRegistration(
        tool_workflow_map=dict(_TOOL_WORKFLOW_MAP),
        default_workflow_name=default_workflow_name,
    )


# ---------------------------------------------------------------------------
# Catalog hydration
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_workflow_registry() -> WorkflowRegistry:
    """Return the shared workflow registry, hydrated from the JSON catalog.

    Reads ``starting_workflows.json`` directly (single source of truth) and
    populates :data:`WorkflowNames` on first call. The path can be overridden
    via the ``LUNGO_WORKFLOWS_JSON`` environment variable (useful for tests).
    """
    path = _workflows_json_path()
    if not path.is_file():
        raise FileNotFoundError(f"Starting workflows data file not found: {path}")

    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to decode {path}: {exc}") from exc

    if not isinstance(data, list):
        raise RuntimeError(
            f"Expected a JSON array in {path}, got {type(data).__name__}"
        )

    catalog: dict[str, WorkflowIdentity] = {}
    for idx, entry in enumerate(data):
        if not isinstance(entry, dict):
            logger.warning("Skipping non-object workflow entry at index %d", idx)
            continue
        name = entry.get("name")
        pattern = entry.get("pattern")
        use_case = entry.get("use_case")
        if not (isinstance(name, str) and isinstance(pattern, str) and isinstance(use_case, str)):
            logger.warning(
                "Skipping workflow at index %d: missing name/pattern/use_case", idx,
            )
            continue
        if name in catalog:
            logger.warning(
                "Duplicate workflow name %r at index %d; overwriting previous entry",
                name, idx,
            )
        catalog[name] = WorkflowIdentity(
            workflow_name=name,
            pattern=pattern,
            use_case=use_case,
        )

    if not catalog:
        raise RuntimeError(
            f"Workflow catalog is empty — no valid entries loaded from {path}"
        )

    logger.info("Loaded %d workflow(s) from %s", len(catalog), path)

    global WorkflowNames
    WorkflowNames = _build_workflow_names(catalog)

    return WorkflowRegistry(catalog)
