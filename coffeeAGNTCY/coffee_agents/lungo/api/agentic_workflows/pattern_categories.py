# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Static catalog data for agentic design pattern categories.

Display names are read from the H1 headings in ``docs/categories/*.md`` so the
HTTP catalog stays aligned with the category reference docs.
"""

from __future__ import annotations

from pathlib import Path

_CATEGORY_DOCS_DIR = Path(__file__).resolve().parent / "docs" / "categories"


def _load_pattern_category_names() -> list[str]:
    names: list[str] = []
    for path in sorted(_CATEGORY_DOCS_DIR.glob("*.md")):
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        if first_line.startswith("# "):
            names.append(first_line[2:].strip())
    return names


PATTERN_CATEGORIES: list[str] = _load_pattern_category_names()
