---
name: uv-lock-sync
description: >-
  Every pyproject.toml in this repo must have a sibling uv.lock that is in
  sync with it. Checked by `task locks:check`
  (scripts/checks/check_uv_locks.bash), which also runs as part of
  `task check:all` in .github/workflows/checks.yaml.
---

# uv lock sync

## Rule

Every git-tracked `pyproject.toml` has a committed `uv.lock` next to it,
and `uv lock --check` passes for it: editing dependencies (or anything
else that affects resolution) in `pyproject.toml` means re-running `uv
lock` and committing the result in the same change.

A `pyproject.toml` that is not a uv project opts out with a
`# uv-lock-exempt: <reason>` comment in the file; the reason is required,
the same opt-out shape [pinned-external-references.md](pinned-external-references.md)
uses for `# pin-exempt:`.

## Why

A stale lock means CI, Docker builds, and developers silently resolve
different dependency versions than the ones reviewed, or fail later on
`uv sync --locked`. Renovate and hand edits both change `pyproject.toml`
without necessarily touching the lock, so only a standing check catches the
drift at review time.

## How to apply

- To check the whole repo: `task locks:check` (wraps
  [scripts/checks/check_uv_locks.bash](../../../scripts/checks/check_uv_locks.bash),
  see [Taskfile.yaml](../../../Taskfile.yaml)). To fix a failure, run `uv
  lock` in the named directory.
- CI enforces this on every push/PR: `task check:all` in
  [.github/workflows/checks.yaml](../../../.github/workflows/checks.yaml)
  runs `locks:check` alongside every other standing check. uv itself is
  pinned in [scripts/lib/versions.sh](../../../scripts/lib/versions.sh) and
  installed by `scripts/setup.sh`.
- See the `checking-uv-locks` skill for the full workflow.
