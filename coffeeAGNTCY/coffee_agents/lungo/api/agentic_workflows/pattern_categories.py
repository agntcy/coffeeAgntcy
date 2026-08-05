# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Static catalog data for agentic design pattern categories.

Display names are read from the H1 headings in ``docs/categories/*.md`` so the
HTTP catalog stays aligned with the category reference docs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_CATEGORY_DOCS_DIR = Path(__file__).resolve().parent / "docs" / "categories"


@dataclass(frozen=True, slots=True)
class PatternCategoryRecord:
    slug: str
    name: str


def _load_pattern_category_records() -> list[PatternCategoryRecord]:
    records: list[PatternCategoryRecord] = []
    for path in sorted(_CATEGORY_DOCS_DIR.glob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or not lines[0].startswith("# "):
            continue
        name = lines[0][2:].strip()
        records.append(PatternCategoryRecord(slug=path.stem, name=name))
    return records


PATTERN_CATEGORY_RECORDS: list[PatternCategoryRecord] = _load_pattern_category_records()
PATTERN_CATEGORIES: list[str] = [record.name for record in PATTERN_CATEGORY_RECORDS]
PATTERN_CATEGORY_BY_NAME: dict[str, PatternCategoryRecord] = {
    record.name: record for record in PATTERN_CATEGORY_RECORDS
}
