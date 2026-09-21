# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Load pattern reference markdown from ``docs/patterns/``.

Canonical display names and legacy normalized slugs resolve through the pattern
registry, so an unknown identifier is a plain miss and caller input never reaches
the filesystem.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from api.agentic_workflows.patterns import (
    PATTERN_DOCS_DIR,
    resolve_pattern_record,
)


@dataclass(frozen=True, slots=True)
class ParsedPatternDocumentation:
    slug: str
    name: str
    title: str | None
    pattern_category: str
    full_markdown: str


def pattern_documentation_dir() -> Path:
    return PATTERN_DOCS_DIR


def load_pattern_documentation(
    pattern_name: str,
) -> ParsedPatternDocumentation | None:
    record = resolve_pattern_record(pattern_name)
    if record is None:
        return None
    path = pattern_documentation_dir() / f"{record.slug}.md"
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    title = lines[0][2:].strip() if lines and lines[0].startswith("# ") else None
    return ParsedPatternDocumentation(
        slug=record.slug,
        name=record.name,
        title=title,
        pattern_category=record.pattern_category,
        full_markdown=raw,
    )
