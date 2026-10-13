# Proposal

## Why

Renovate's grouped Helm PR #832 left `corto-local-cluster`'s `Chart.lock`
out of the update: `helm dependency update` could not resolve three
`file://` sibling charts, because the exact versions pinned in the
umbrella's `Chart.yaml` (0.2.0, 0.2.0, 0.1.0) no longer matched the
siblings' own versions (0.2.1, 0.2.1, 0.1.1), and the committed lock still
recorded 0.1.0. The drift was old, and nothing in the repo caught it: the
Helm version-bump check only asks whether a chart's own `version:` moved,
and it was satisfied because the siblings had each been bumped with their
own changes. The umbrella chart itself had not changed, so there was
nothing to flag. The repo has an equivalent lock-sync check for uv
(`locks:check`) but none for Helm.

## What Changes

- **A Helm lock check**, `task helm:check-locks`, that re-runs `helm
  dependency update` in a scratch copy of every tracked chart and compares
  each resulting `Chart.lock` with the committed one (ignoring the
  `generated:` timestamp). It catches third-party drift, `file://` sibling
  drift and missing locks, never rewrites a committed file, and fails with
  an explanatory message when the update itself cannot resolve a sibling.
- **A lock update operation**, `task helm:update-locks`, running the same
  `helm dependency update` in place for every chart that declares
  dependencies, so the fix for a failing check, and the "dependency update
  for local cluster charts" Renovate performs, exist as a local command.
- **helm joins the repo-local toolchain**: pinned in
  `scripts/lib/versions.sh` (tracked by Renovate through the existing
  annotation), installed by `scripts/setup.sh` into `.tools/bin`
  unconditionally so CI's `--lint-only` bootstrap has it. helm's cache,
  config, and data directories live under `.tools/helm/`.
- **The check joins `task check:all`** as the twelfth parallel check, so
  `checks.yaml` enforces it with no workflow change.
- Full five-layer pipeline: scripts, tasks, a `checking-helm-chart-locks`
  skill, CI via `check_all.bash`, and a `helm-chart-lock-sync` rule, all
  indexed in `AGENTS.md`, with `CONTRIBUTING.md`, the setup skill, the
  pre-finalize checks rule, and the workflows README updated to match.

## Capabilities

### New Capabilities

- `helm-chart-lock-sync`: the requirement that every Helm chart declaring
  dependencies has a committed `Chart.lock` that reproduces under `helm
  dependency update`, the update operation that regenerates it, and the
  layers that enforce and document both.

### Modified Capabilities

- `repo-tooling`: the pinned toolchain gains `helm` (and the requirement's
  tool list also gains `uv`, which `setup.sh` already installed but the
  requirement never named).

## Impact

- New: `scripts/helm/update_chart_locks.bash`,
  `scripts/checks/check_helm_chart_locks.bash`, their bats tests, two
  Taskfile tasks, one skill, one rule.
- Changed: `scripts/lib/versions.sh`, `scripts/setup.sh`,
  `scripts/lib/platform.sh` (comment), `scripts/checks/check_all.bash`,
  `Taskfile.yaml`, `AGENTS.md`, `CONTRIBUTING.md`, the setup skill,
  `pre-finalize-checks.md`, `.github/workflows/README.md`, and the setup,
  versions, and check_all tests.
- `checks.yaml` is unchanged. The new check needs network access to chart
  repositories and registries (ghcr.io, Docker Hub, https chart repos),
  like `locks:check` needs the Python indexes.
- No chart's `Chart.yaml` or `Chart.lock` changes; this only adds
  tooling.
