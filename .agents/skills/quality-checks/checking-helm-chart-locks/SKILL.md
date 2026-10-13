---
name: checking-helm-chart-locks
description: >-
  Runs task helm:check-locks to confirm every Helm chart with dependencies
  has a Chart.lock in sync with its Chart.yaml, and regenerates any that
  drifted with task helm:update-locks. Use after adding, removing, or
  re-pinning a chart dependency, after bumping a chart that another chart
  pulls in through file://, or before finishing any change inside a Helm
  chart directory.
---

# Checking Helm chart locks

## What this skill does

Runs `task helm:check-locks` (defined in [Taskfile.yaml](../../../../Taskfile.yaml),
wrapping
[scripts/checks/check_helm_chart_locks.bash](../../../../scripts/checks/check_helm_chart_locks.bash))
to re-run `helm dependency update` in a scratch copy of every tracked chart
and compare each resulting `Chart.lock` with the committed one. This is the
same check `task check:all` runs as part of
[checks.yaml](../../../../.github/workflows/checks.yaml). See
[.agents/rules/quality/helm-chart-lock-sync.md](../../../rules/quality/helm-chart-lock-sync.md)
for the underlying rule.

## Workflow

```
- [ ] 1. Run: task helm:check-locks
- [ ] 2. For each flagged chart, run `task helm:update-locks` (it
        regenerates every lock in one go) and commit the updated
        Chart.lock files together with the Chart.yaml change
- [ ] 3. If the failure says `helm dependency update` itself failed and
        names a file:// subchart, the version pinned in that chart's
        Chart.yaml no longer matches the sibling chart's own version:
        update the pin to the sibling's current version, then step 2
- [ ] 4. Bump the version of every chart whose Chart.yaml or Chart.lock
        changed, and run task helm:check-versions (see the
        checking-helm-chart-version-bumps skill)
- [ ] 5. Re-run task helm:check-locks to confirm it's clean
```

## Notes

- The check never rewrites a committed lock; only `task helm:update-locks`
  does.
- Both tasks resolve against the chart repositories and registries, so they
  need network access. helm's cache and config live under `.tools/helm/`.
- helm is the repo-local pinned binary from `./scripts/setup.sh`
  (`.tools/bin/helm`); run `source scripts/env.sh` or `task setup` first if
  it reports helm not found.
