# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Resolve ``docs/workflows/{slug}.md`` from catalog workflow names and parse ``##`` sections.

The *slug* is only used for on-disk filenames. HTTP paths use the catalog ``Workflow.name``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Characters allowed in derived slugs / markdown basenames under ``docs/workflows/``.
_SLUG_RE = re.compile(r"^[a-z0-9_+\-&]+$")

_WORKFLOW_DOCS_DIR = Path(__file__).resolve().parent / "docs" / "workflows"


@dataclass(frozen=True)
class ParsedWorkflowDocumentation:
    slug: str
    title: str | None
    sections: list[tuple[str, str, str]]  # anchor, heading, body_markdown
    full_markdown: str


def workflow_documentation_dir() -> Path:
    return _WORKFLOW_DOCS_DIR


def is_safe_workflow_documentation_slug(slug: str) -> bool:
    if not slug or len(slug) > 256:
        return False
    return bool(_SLUG_RE.fullmatch(slug))


def workflow_name_to_documentation_slug(name: str) -> str:
    """Map catalog ``Workflow.name`` to markdown basename (without ``.md``)."""
    s = name.strip().lower()
    for ch in ("\u2013", "\u2014", "\u2212"):  # en dash, em dash, minus sign
        s = s.replace(ch, "_")
    s = s.replace(" ", "_")
    s = s.replace("(", "_").replace(")", "_")
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def _anchor_from_heading(heading: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-") or "section"
    anchor = base
    n = 2
    while anchor in used:
        anchor = f"{base}-{n}"
        n += 1
    used.add(anchor)
    return anchor


def parse_workflow_documentation_markdown(
    markdown_text: str, *, slug: str
) -> ParsedWorkflowDocumentation:
    text = markdown_text.replace("\r\n", "\n")
    stripped = text.strip()

    title: str | None = None
    if stripped.startswith("# "):
        nl = stripped.find("\n")
        if nl == -1:
            title = stripped[2:].strip()
            stripped = ""
        else:
            title = stripped[2:nl].strip()
            stripped = stripped[nl + 1 :].lstrip("\n")

    section_chunks = re.split(r"(?m)^##\s+", stripped)
    anchor_used: set[str] = set()
    sections: list[tuple[str, str, str]] = []

    preamble = section_chunks[0].strip() if section_chunks else ""
    if preamble:
        sections.append(
            (_anchor_from_heading("preamble", anchor_used), "preamble", preamble)
        )

    for chunk in section_chunks[1:]:
        chunk = chunk.rstrip()
        if not chunk:
            continue
        nl = chunk.find("\n")
        if nl == -1:
            heading, body = chunk.strip(), ""
        else:
            heading, body = chunk[:nl].strip(), chunk[nl + 1 :].lstrip("\n").rstrip()
        sections.append((_anchor_from_heading(heading, anchor_used), heading, body))

    return ParsedWorkflowDocumentation(
        slug=slug,
        title=title,
        sections=sections,
        full_markdown=text,
    )


def resolve_workflow_documentation_path(slug: str) -> Path | None:
    if not is_safe_workflow_documentation_slug(slug):
        return None
    base = _WORKFLOW_DOCS_DIR.resolve()
    candidate = (base / f"{slug}.md").resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


def load_parsed_workflow_documentation(slug: str) -> ParsedWorkflowDocumentation | None:
    path = resolve_workflow_documentation_path(slug)
    if path is None:
        return None
    raw = path.read_text(encoding="utf-8")
    return parse_workflow_documentation_markdown(raw, slug=slug)
