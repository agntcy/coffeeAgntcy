---
name: helm-chart-lock-sync
description: >-
  Every Helm chart in this repo that declares dependencies must have a
  committed Chart.lock that is in sync with them, including the versions of
  any file:// sibling charts it pulls in. Checked by `task
  helm:check-locks` (scripts/checks/check_helm_chart_locks.bash), which
  also runs as part of `task check:all` in .github/workflows/checks.yaml.
  Regenerate with `task helm:update-locks`.
---

# Helm chart lock sync

## Rule

Every git-tracked Helm chart whose `Chart.yaml` has a `dependencies:` list
has a committed `Chart.lock` next to it, and re-running `helm dependency
update` for it reproduces that lock (ignoring the `generated:` timestamp).
That covers both kinds of dependency:

- **Third-party** charts from OCI and https repositories: re-pinning one in
  `Chart.yaml` means refreshing the lock in the same change.
- **Sibling** charts referenced as `file://../<chart>`: the version pinned
  in the umbrella's `Chart.yaml` must match the sibling's own `version:`
  exactly, so bumping a sibling chart (which the
  [helm-chart-version-bump](helm-chart-version-bump.md) rule requires for
  any content change) also means updating the pin and the lock of every
  chart that depends on it.

## Why

A stale lock means `helm dependency build`, CI packaging, and Renovate
resolve different dependency versions than the ones reviewed, or fail
outright. Nothing else catches it: the version-bump check only looks at
whether a chart's own `version:` moved, and `helm dependency list` only
compares `Chart.yaml` with an uncommitted `charts/` directory, so it reports
every dependency as missing whether or not the lock is stale. It also
fails silently for a long time: a `file://` pin that fell behind its sibling
(`corto-local-cluster` pinned `corto-exchange` 0.2.0 while the sibling was at
0.2.1) only surfaced when Renovate's own `helm dependency update` could not
resolve it and left the lock out of its PR.

The check re-runs the real update in a scratch copy of every tracked chart,
so it catches whatever `helm dependency update` itself would change or fail
on, instead of approximating it.

## How to apply

- After editing a chart's `dependencies:`, or bumping a sibling chart that
  another chart pulls in through `file://`, run `task helm:update-locks`
  (wraps
  [scripts/helm/update_chart_locks.bash](../../../scripts/helm/update_chart_locks.bash),
  see [Taskfile.yaml](../../../Taskfile.yaml)) and commit the changed
  `Chart.lock` files with the change. Then bump the version of every chart
  whose `Chart.yaml` or `Chart.lock` changed (`task helm:check-versions`).
- To check the whole repo: `task helm:check-locks` (wraps
  [scripts/checks/check_helm_chart_locks.bash](../../../scripts/checks/check_helm_chart_locks.bash)).
  It never rewrites a committed file, and needs network access to the chart
  repositories and registries.
- CI enforces this on every push/PR: `task check:all` in
  [.github/workflows/checks.yaml](../../../.github/workflows/checks.yaml)
  runs `helm:check-locks` alongside every other standing check. helm itself
  is pinned in [scripts/lib/versions.sh](../../../scripts/lib/versions.sh)
  and installed by `scripts/setup.sh`.
- See the `checking-helm-chart-locks` skill for the full workflow.
