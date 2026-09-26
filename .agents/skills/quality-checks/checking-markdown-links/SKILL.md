---
name: checking-markdown-links
description: >-
  Runs task links:check to find any relative markdown link that doesn't
  resolve to a file that exists, and fixes each one it finds. Use after
  moving, renaming, or removing a file, or before finishing any change
  that edits a markdown link.
---

# Checking markdown links

## What this skill does

Runs `task links:check` (defined in [Taskfile.yaml](../../../../Taskfile.yaml),
wrapping
[scripts/checks/check_markdown_links.bash](../../../../scripts/checks/check_markdown_links.bash))
to scan every git-tracked `*.md` file for a relative `[text](<target>)` link
whose target doesn't resolve to an existing file. This is the same check
`task check:all` runs as part of
[checks.yaml](../../../../.github/workflows/checks.yaml). See
[.agents/rules/quality/markdown-link-integrity.md](../../../rules/quality/markdown-link-integrity.md)
for the underlying rule.

## Workflow

```
- [ ] 1. Run: task links:check
- [ ] 2. For each flagged link, either fix the target path (the file
        moved or was renamed - find its new path) or fix the link text
        (the target was correct but the wrong file was linked)
- [ ] 3. If the target genuinely can't resolve to a real file on purpose
        (a placeholder in illustrative prose, a link to a file this same
        change creates later in a multi-step process), reword it so it
        doesn't look like a real link, or add a trailing
        `<!-- link-exempt: <reason> -->` comment stating why
- [ ] 4. Re-run task links:check to confirm it's clean
```

## Notes

- This only checks that the target *file* exists - it does not follow a
  `#anchor` to confirm a heading with that name actually exists in the
  target file.
- A target starting with `/` is checked from the repo root (matching how
  GitHub itself renders a root-relative link); everything else is checked
  relative to the linking file's own directory - the same convention this
  repo's markdown already follows.
- A link inside backtick-quoted prose illustrating markdown syntax itself
  (e.g. a sentence explaining what a cross-link should look like) is easy
  to mistake for a real link - a `<...>` placeholder segment in the target
  (e.g. `path/<rule>.md`) is skipped for exactly this reason; a link to an
  actual file never needs one.
- After moving or renaming any file this repo's docs might reference,
  running this check is the fast way to confirm nothing was missed -
  faster than grepping for the old path by hand, and it catches links
  grep-based sweeps miss (a relative path that resolves to the wrong file
  after a move, not just an old filename).
