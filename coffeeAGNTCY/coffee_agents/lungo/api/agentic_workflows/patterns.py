# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Registry of architectural patterns backing the pattern reference library.

Records are derived from the reference docs under ``docs/patterns`` so the catalog
and the served markdown cannot drift: the display name is the H1 heading and the
category is the ``**Category:**`` line.

The reference library is the *full* set of patterns. Whether a pattern is also
runnable is a separate fact owned by the workflow catalog - see
:func:`implemented_pattern_names` - not a property of the pattern itself.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from api.agentic_workflows.pattern_categories import PATTERN_CATEGORIES
from api.agentic_workflows.workflow_documentation import (
    parse_pattern_category_from_section_body,
    workflow_name_to_documentation_slug,
)
from schema.types import Workflow

PATTERN_DOCS_DIR = Path(__file__).resolve().parent / "docs" / "patterns"


@dataclass(frozen=True, slots=True)
class PatternRecord:
    slug: str
    name: str
    pattern_category: str


def _load_pattern_records(
    pattern_docs_dir: Path = PATTERN_DOCS_DIR,
) -> list[PatternRecord]:
    paths = sorted(pattern_docs_dir.glob("*.md"))
    if not paths:
        raise ValueError(f"Pattern documentation directory is empty: {pattern_docs_dir}")

    records: list[PatternRecord] = []
    names: set[str] = set()
    for path in paths:
        markdown = path.read_text(encoding="utf-8")
        lines = markdown.splitlines()
        name = lines[0][2:].strip() if lines and lines[0].startswith("# ") else ""
        category = parse_pattern_category_from_section_body(markdown)
        if not name or category is None:
            raise ValueError(
                f"Invalid pattern document {path}: expected a non-empty H1 heading "
                "and a non-empty '**Category:**' line"
            )
        if name in names:
            raise ValueError(f"Duplicate pattern name {name!r} in {pattern_docs_dir}")
        if category not in PATTERN_CATEGORIES:
            raise ValueError(
                f"Unknown pattern category {category!r} in {path}; "
                "add it to docs/categories first"
            )
        names.add(name)
        records.append(
            PatternRecord(slug=path.stem, name=name, pattern_category=category)
        )
    records.sort(key=lambda record: record.name)
    return records


PATTERN_RECORDS: list[PatternRecord] = _load_pattern_records()
PATTERNS: list[str] = [record.name for record in PATTERN_RECORDS]
PATTERN_BY_NAME: dict[str, PatternRecord] = {
    record.name: record for record in PATTERN_RECORDS
}
PATTERN_BY_SLUG: dict[str, PatternRecord] = {
    record.slug: record for record in PATTERN_RECORDS
}


def resolve_pattern_record(pattern_identifier: str) -> PatternRecord | None:
    """Resolve a canonical display name or legacy normalized slug."""
    by_name = PATTERN_BY_NAME.get(pattern_identifier)
    if by_name is not None:
        return by_name
    slug = workflow_name_to_documentation_slug(pattern_identifier)
    return PATTERN_BY_SLUG.get(slug)


def implemented_pattern_names(
    workflows: Mapping[str, Workflow],
) -> frozenset[str]:
    """Return the pattern names that have at least one workflow in ``workflows``."""
    return frozenset(workflow.pattern for workflow in workflows.values())
