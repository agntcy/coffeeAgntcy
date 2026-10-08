---
name: checking-uv-locks
description: >-
  Runs task locks:check to confirm every pyproject.toml has a sibling
  uv.lock that is in sync with it, and fixes any that drifted. Use after
  adding, removing, or changing a Python dependency or other
  pyproject.toml setting that affects resolution, or before finishing any
  change that touches pyproject.toml or uv.lock.
---

# Checking uv locks

## What this skill does

Runs `task locks:check` (defined in [Taskfile.yaml](../../../../Taskfile.yaml),
wrapping
[scripts/checks/check_uv_locks.bash](../../../../scripts/checks/check_uv_locks.bash))
to run `uv lock --check` next to every git-tracked `pyproject.toml`. This is
the same check `task check:all` runs as part of
[checks.yaml](../../../../.github/workflows/checks.yaml). See
[.agents/rules/quality/uv-lock-sync.md](../../../rules/quality/uv-lock-sync.md)
for the underlying rule.

## Workflow

```
- [ ] 1. Run: task locks:check
- [ ] 2. For each flagged project, run `uv lock` in that directory (the
        failure message names it) and commit the updated uv.lock together
        with the pyproject.toml change
- [ ] 3. For a pyproject.toml with no sibling uv.lock, run `uv lock` in
        its directory, or, if it is not a uv project, add a
        `# uv-lock-exempt: <reason>` comment to it
- [ ] 4. Re-run task locks:check to confirm it's clean
```

## Notes

- The check never rewrites a lock; only `uv lock` does.
- It resolves against the package indexes, so it needs network access.
- uv is the repo-local pinned binary from `./scripts/setup.sh`
  (`.tools/bin/uv`); run `source scripts/env.sh` or `task setup` first if
  it reports uv not found.
