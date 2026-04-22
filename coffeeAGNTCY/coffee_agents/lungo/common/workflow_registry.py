# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Workflow catalog loading, tool registration, and workflow resolution."""

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


# Catalog source
_DEFAULT_WORKFLOWS_JSON = (
    Path(__file__).resolve().parents[1]
    / "api" / "agentic_workflows" / "starting_workflows.json"
)


def _workflows_json_path() -> Path:
    """Return the catalog path, honoring ``LUNGO_WORKFLOWS_JSON``."""
    override = os.getenv("LUNGO_WORKFLOWS_JSON")
    return Path(override) if override else _DEFAULT_WORKFLOWS_JSON


def _tool_identity_key(obj: Any) -> str:
    """Return a stable tool key from common callable wrapper attributes."""
    key = (
        getattr(obj, "name", None)
        or getattr(obj, "__name__", None)
        or getattr(getattr(obj, "__wrapped__", None), "__name__", None)
    )
    if not isinstance(key, str) or not key:
        raise TypeError(f"Cannot derive tool identity key from {obj!r}")
    return key


def _slugify_const(name: str) -> str:
    """Convert workflow name to a Python-safe uppercase constant."""
    s = re.sub(r"[^0-9A-Za-z]+", "_", name).strip("_").upper()
    if not s:
        return "WF_UNKNOWN"
    if s[0].isdigit():
        s = "WF_" + s
    return s


def _build_workflow_names(catalog: dict[str, WorkflowIdentity]) -> SimpleNamespace:
    """Build ``WorkflowNames`` as uppercase constant name -> workflow name."""
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


WorkflowNames: SimpleNamespace = SimpleNamespace()


def workflow_names() -> SimpleNamespace:
    """Return generated workflow name constants, hydrating registry if needed."""
    get_workflow_registry()
    return WorkflowNames


_TOOL_WORKFLOW_MAP: dict[str, str] = {}


def register_workflow(workflow_name: str):
    """Decorator: map a tool object to a catalog workflow name."""
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
    """Build a ``ClientCallContext`` with the normalized tool key."""
    return ClientCallContext(state={"tool": _tool_identity_key(tool_obj), **extra})


@dataclass(frozen=True)
class WorkflowRegistration:
    """Tool-to-workflow mapping plus optional resolver default."""

    tool_workflow_map: dict[str, str] = field(default_factory=dict)
    default_workflow_name: str | None = None


class WorkflowRegistry:
    """Lookup workflow metadata by name."""

    def __init__(self, workflows_by_name: dict[str, WorkflowIdentity]) -> None:
        if not workflows_by_name:
            raise ValueError("workflows_by_name must not be empty")
        self._workflows_by_name = dict(workflows_by_name)

    def get(self, workflow_name: str) -> WorkflowIdentity:
        """Return metadata for ``workflow_name`` or raise ``KeyError``."""
        try:
            return self._workflows_by_name[workflow_name]
        except KeyError as exc:
            raise KeyError(f"Unknown workflow name: {workflow_name}") from exc


class ToolWorkflowResolver:
    """Resolve tool names to workflow metadata."""

    def __init__(
        self,
        *,
        registry: WorkflowRegistry,
        registration: WorkflowRegistration,
    ) -> None:
        self._validate_registration(registry, registration)
        self._registry = registry
        self._registration = registration

    @staticmethod
    def _validate_registration(
        registry: WorkflowRegistry,
        registration: WorkflowRegistration,
    ) -> None:
        if not registration.tool_workflow_map and registration.default_workflow_name is None:
            raise ValueError(
                "WorkflowRegistration must declare at least one tool workflow "
                "or a default_workflow_name"
            )
        if registration.default_workflow_name is not None:
            registry.get(registration.default_workflow_name)
        for workflow_name in registration.tool_workflow_map.values():
            registry.get(workflow_name)

    def resolve(self, tool_name: str | None) -> WorkflowIdentity:
        """Resolve a tool name to workflow metadata."""
        mapping = self._registration.tool_workflow_map
        if tool_name and tool_name in mapping:
            return self._registry.get(mapping[tool_name])

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
    """Snapshot current ``@register_workflow`` registrations."""
    if not _TOOL_WORKFLOW_MAP:
        raise RuntimeError(
            "No tools registered via @register_workflow. "
            "Ensure the tool module is imported before building the resolver."
        )
    return WorkflowRegistration(
        tool_workflow_map=dict(_TOOL_WORKFLOW_MAP),
        default_workflow_name=default_workflow_name,
    )


@lru_cache(maxsize=1)
def get_workflow_registry() -> WorkflowRegistry:
    """Load and cache the workflow registry from JSON catalog."""
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
