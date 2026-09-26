---
name: markdown-link-integrity
description: >-
  Every relative markdown link in this repo must resolve to a file that
  actually exists. Checked by `task links:check`
  (scripts/checks/check_markdown_links.bash), which also runs as part of
  `task check:all` in .github/workflows/checks.yaml.
---

# Markdown link integrity

## Rule

Every relative `[text](<target>)` (or image `![alt](<src>)`) link in a markdown
file in this repo must resolve to a file that exists on disk - a link to
`http(s)://`/`mailto:` addresses or a bare in-page `#anchor` isn't covered
by this rule (nothing in this repo can verify those), but anything that
looks like a path into this repo's own working tree must be a real path.

When moving, renaming, or removing a file, update or remove every link
that pointed at its old path in the same change - don't leave the next
reader (human or agent) to discover a dangling link by clicking it.

## Why

A markdown link is a promise that following it lands somewhere real. A
grep-based sweep for a file's old name after a move catches most stale
references, but not all of them - a relative link can silently resolve to
the *wrong* file after a move (both the old and new location happen to
exist, just not the one the author meant) without ever containing the old
name as a string. This exact failure mode showed up twice while
reorganizing `.agents/rules/`/`.agents/skills/` into category
subdirectories (see the `repo-tree-reorganization` change): a blanket
"bump every relative link by one directory level" fix correctly repaired
links to files that moved to a *different* new location, but broke
links between two files that moved *together* into the same new
location, since their relative distance from each other never changed.
Neither mistake showed up in a plain grep for an old path - only actually
resolving each link against the filesystem caught them.

## How to apply

- To check the whole repo: `task links:check` (wraps
  [scripts/checks/check_markdown_links.bash](../../../scripts/checks/check_markdown_links.bash),
  see [Taskfile.yaml](../../../Taskfile.yaml)). It reports every dangling
  link by file and line; there's no auto-fix, since the correct fix (the
  right new path, or removing the link) requires knowing what the author
  meant.
- CI enforces this on every push/PR: `task check:all` in
  [.github/workflows/checks.yaml](../../../.github/workflows/checks.yaml)
  runs `links:check` alongside every other standing check.
- After moving or renaming any file, run `task links:check` before
  considering the change done - don't rely on a grep for the old filename
  alone; see [.agents/rules/formatting/organize-large-collections.md](../formatting/organize-large-collections.md)'s
  own "How to apply" note on this.
- A target containing a `<...>` placeholder segment (e.g. `path/<rule>.md`
  in prose illustrating a naming pattern) or a GitHub web path
  (`/<owner>/<repo>/blob/...`) is intentionally not checked - neither is a
  path into this repo's own working tree. Anything else that genuinely
  can't resolve to a real file needs a trailing
  `<!-- link-exempt: <reason> -->` comment stating why, the same opt-out
  shape [pinned-external-references.md](pinned-external-references.md)
  already uses for `# pin-exempt:`.
- Covers only inline links (`[text](<target>)`) - reference-style links
  (`[text][ref]` with a separate `[ref]: <target>` definition) aren't
  scanned, since this repo doesn't use that style anywhere today. If that
  changes, extend
  [scripts/checks/check_markdown_links.bash](../../../scripts/checks/check_markdown_links.bash)
  to cover it rather than leaving it as a silent gap.
- See the `checking-markdown-links` skill for the full workflow.
