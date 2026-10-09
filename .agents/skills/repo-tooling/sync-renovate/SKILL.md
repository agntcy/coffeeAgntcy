---
name: sync-renovate
description: >-
  Runs Renovate against this repo via task renovate:sync to open or update
  dependency update PRs. Use when asked to run, debug, or reason about the
  dependency update sync, or to change what Renovate does (renovate.json).
---

# Sync Renovate

## When to use

When asked to run the dependency update sync by hand, to debug why a
dependency update PR did or didn't appear, or to change Renovate's
behavior. In normal operation nobody runs this locally: the
[`Renovate` workflow](../../../../.github/workflows/renovate.yaml) runs
`task renovate:sync` every six hours (and on manual dispatch), the only
caller today.

## What it does

`task renovate:sync` (defined in
[Taskfile.yaml](../../../../Taskfile.yaml), wrapping
[scripts/renovate/sync_renovate.bash](../../../../scripts/renovate/sync_renovate.bash))
runs the repo-local `renovate` binary, installed into `.tools/bin/` by
`scripts/setup.sh` at the version pinned in [scripts/lib/versions.sh](../../../../scripts/lib/versions.sh)
(see the `manage-repo-tooling` skill to bump it). Behavior is driven
entirely by [renovate.json](../../../../renovate.json) and the
`RENOVATE_*` / `GITHUB_COM_TOKEN` environment variables the caller sets;
neither the task nor the script adds any configuration of its own.

A version bump in `scripts/lib/versions.sh` also needs a fresh
`scripts/lib/checksums.txt` and npm lockfile, which `setup.sh` verifies
against. `renovate.json` handles that with a `postUpgradeTasks` entry
running `scripts/tools/update_checksums.bash` and
`scripts/tools/update_npm_lock.bash` (once per branch), and the workflow
sets `RENOVATE_ALLOWED_COMMANDS` to allow only those two commands - adding
another post-upgrade command means widening that allowlist in
`.github/workflows/renovate.yaml` too.

This is a generative action, not a standing check, so it isn't part of
`task check:all`; the `Renovate` workflow runs it on a schedule instead,
and it has no separate rule. See "Scheduled generative operations" in the
"Known exceptions" of
[`.agents/rules/meta/repo-operation-pipeline.md`](../../../rules/meta/repo-operation-pipeline.md).

## Workflow

```
- [ ] 1. Run: ./scripts/setup.sh, then source scripts/env.sh (puts the pinned renovate on PATH)
- [ ] 2. To validate a config change without touching GitHub, run: renovate-config-validator renovate.json
- [ ] 3. To run a sync for real, ask the user first: it creates and updates branches and PRs on the remote repo. Set the same RENOVATE_* variables .github/workflows/renovate.yaml sets (RENOVATE_PLATFORM, RENOVATE_TOKEN, GITHUB_COM_TOKEN, ...), then run: task renovate:sync
- [ ] 4. Prefer RENOVATE_DRY_RUN=full for a local run that only logs what it would do
```

## Rules

- Never run a non-dry-run sync without the user's explicit go-ahead each
  time - it writes to a remote system.
- Tool version pins carry `# renovate:` annotations in
  `scripts/lib/versions.sh`; keep them in that shape so Renovate keeps
  tracking them.
