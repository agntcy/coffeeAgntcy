# Proposal

## Why

The `repo-tooling` spec's first requirement lists the tools `task setup`
installs and the directories `scripts/env.sh` puts on `PATH`. It predates
two later additions: `bats` (installed into `.tools/bats/` by the
bash-script-testing change) and `renovate` (installed with the pinned
Node.js). The spec therefore under-describes what `scripts/setup.sh` and
`scripts/env.sh` actually do, found by a repo-wide self-audit.

## What Changes

- Modify the requirement "A repo-local toolchain installs without touching
  the global system" so the tool list includes `bats` and `renovate`, and
  `source scripts/env.sh` is required to put `.tools/bats/bin` on `PATH`
  alongside `.tools/bin` and `.tools/node/bin`.
- No code change: `scripts/setup.sh`, `scripts/env.sh`, `Taskfile.yaml` and
  the `setup-repo-tooling` skill already behave and read this way.

## Impact

- Affected spec: `repo-tooling`.
- No script, task, skill, workflow or rule changes.
