# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Workflow catalog lookup for A2A event middleware.

Workflow identity (workflow_name + instance_id) is propagated to the
middleware via OpenTelemetry baggage (see ``common.workflow_context_prop``).
This module's job is to resolve a propagated workflow_name to its
catalog metadata (pattern + use_case) for inclusion on emitted events.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger("lungo.common.workflow_catalog")


@dataclass(frozen=True)
class WorkflowMetadata:
	"""Workflow descriptive metadata sourced from the workflow catalog."""

	workflow_name: str
	pattern: str
	use_case: str
	scenario: str


_DEFAULT_WORKFLOWS_JSON = (
	Path(__file__).resolve().parents[2]
	/ "api"
	/ "agentic_workflows"
	/ "starting_workflows.json"
)


def _workflows_json_path() -> Path:
	"""Return the catalog path, honoring LUNGO_WORKFLOWS_JSON."""
	override = os.getenv("LUNGO_WORKFLOWS_JSON")
	return Path(override) if override else _DEFAULT_WORKFLOWS_JSON


@lru_cache(maxsize=1)
def _load_catalog() -> dict[str, WorkflowMetadata]:
	"""Load and cache the workflow catalog from JSON."""
	path = _workflows_json_path()
	if not path.is_file():
		raise FileNotFoundError(f"Starting workflows data file not found: {path}")

	try:
		with open(path, encoding="utf-8") as fh:
			data = json.load(fh)
	except json.JSONDecodeError as exc:
		raise RuntimeError(f"Failed to decode {path}: {exc}") from exc

	if not isinstance(data, list):
		raise RuntimeError(f"Expected a JSON array in {path}, got {type(data).__name__}")

	catalog: dict[str, WorkflowMetadata] = {}
	for idx, entry in enumerate(data):
		if not isinstance(entry, dict):
			logger.warning("Skipping non-object workflow entry at index %d", idx)
			continue
		name = entry.get("name")
		pattern = entry.get("pattern")
		use_case = entry.get("use_case")
		scenario = entry.get("scenario")
		if not (
			isinstance(name, str)
			and isinstance(pattern, str)
			and isinstance(use_case, str)
			and isinstance(scenario, str)
		):
			logger.warning(
				"Skipping workflow at index %d: missing name/pattern/use_case/scenario",
				idx,
			)
			continue
		if not isinstance(scenario, str) or not scenario.strip():
			scenario = use_case
		if name in catalog:
			logger.warning(
				"Duplicate workflow name %r at index %d; overwriting previous entry",
				name,
				idx,
			)
		catalog[name] = WorkflowMetadata(
			workflow_name=name,
			pattern=pattern,
			use_case=use_case,
			scenario=scenario,
		)

	if not catalog:
		raise RuntimeError(
			f"Workflow catalog is empty - no valid entries loaded from {path}"
		)

	logger.info("Loaded %d workflow(s) from %s", len(catalog), path)
	return catalog


def lookup_workflow(workflow_name: str | None) -> WorkflowMetadata | None:
	"""Return WorkflowMetadata for ``workflow_name`` or None if not in catalog.

	Returns None when ``workflow_name`` is falsy or absent from the catalog.
	Callers log + skip emission rather than raising.
	"""
	if not workflow_name:
		return None
	return _load_catalog().get(workflow_name)
