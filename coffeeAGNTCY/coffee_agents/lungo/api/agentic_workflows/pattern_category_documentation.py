# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Load pattern category reference markdown from ``docs/categories/``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from api.agentic_workflows.pattern_categories import (
    PATTERN_CATEGORY_BY_NAME,
    PATTERN_CATEGORY_RECORDS,
)


@dataclass(frozen=True, slots=True)
class ParsedPatternCategoryDocumentation:
    slug: str
    name: str
    title: str | None
    full_markdown: str


def pattern_category_documentation_dir() -> Path:
    return Path(__file__).resolve().parent / "docs" / "categories"


def load_pattern_category_documentation(
    category_name: str,
) -> ParsedPatternCategoryDocumentation | None:
    record = PATTERN_CATEGORY_BY_NAME.get(category_name)
    if record is None:
        return None
    path = pattern_category_documentation_dir() / f"{record.slug}.md"
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    title = lines[0][2:].strip() if lines and lines[0].startswith("# ") else None
    return ParsedPatternCategoryDocumentation(
        slug=record.slug,
        name=record.name,
        title=title,
        full_markdown=raw,
    )


def all_pattern_category_names() -> list[str]:
    return [record.name for record in PATTERN_CATEGORY_RECORDS]
