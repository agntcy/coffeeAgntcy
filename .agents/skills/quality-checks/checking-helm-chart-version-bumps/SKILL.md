---
name: checking-helm-chart-version-bumps
description: >-
  Checks whether any Helm chart under
  coffeeAGNTCY/coffee_agents/{corto,lungo}/deployment/helm/*/ has content
  changes not covered by a later Chart.yaml `version:` bump, anywhere in
  that chart's history, and bumps any that didn't. Use when editing files
  inside a Helm chart directory, before finishing such a change, when
  asked to check or audit Helm chart versions, or when performing
  docs/RELEASE-OPS.md Step 0 before a release.
---

# Checking Helm chart version bumps

## What this skill does

Runs `task helm:check-versions` (defined in
[Taskfile.yaml](../../../../Taskfile.yaml), wrapping
[scripts/checks/check_helm_chart_versions.bash](../../../../scripts/checks/check_helm_chart_versions.bash))
to find every Helm chart whose contents changed - anywhere in that
chart's history, not scoped to any release tag - without a later
`Chart.yaml` `version:` bump covering that change, then bumps each
flagged chart by ordinary semver judgment. This automates
[docs/RELEASE-OPS.md](../../../../docs/RELEASE-OPS.md) Step 0 instead of
its old manual per-chart snippet, and is the same check `task check:all`
runs as part of
[checks.yaml](../../../../.github/workflows/checks.yaml). See
[.agents/rules/quality/helm-chart-version-bump.md](../../../rules/quality/helm-chart-version-bump.md)
for the underlying rule.

## Workflow

```
- [ ] 1. Run: task helm:check-versions (no arguments - it always checks
        every chart's whole history as of HEAD)
- [ ] 2. For each flagged chart, read what changed: git log -- <chart-dir>
- [ ] 3. Every flagged chart needs a bump - the `helm:check-versions` check
        is a CI merge gate with no trivial-diff exception, so even a pure
        comment/whitespace-only diff still needs (at least) a patch bump
- [ ] 4. Pick the bump level per ordinary semver:
        - patch: backward-compatible fix, internal tweak
        - minor: new value/template/feature, still backward compatible
        - major: breaking change to the chart's values.yaml interface or
          resource shape
- [ ] 5. Edit the flagged chart's Chart.yaml `version:` field (and any
        umbrella Chart.yaml dependency pin that references it)
- [ ] 6. Re-run task helm:check-versions to confirm every flagged chart is
        now clean
```

## Notes

- Charts are versioned independently - one chart's content change never
  requires bumping a sibling chart's version, even under the same umbrella
  repo.
- `appVersion` tracks the application image version, not the chart
  content - only bump it if the chart's default image tag/reference
  actually changed. Don't conflate it with `version:`.
- A chart's very first commit (adding its contents and setting its
  starting `version:` in the same commit) is never flagged - there's
  nothing earlier to compare it against.
- The check doesn't follow a chart directory's renames (a `git log`
  limitation, not a design choice) - a rename can under-report content
  changes from before it. This is a stated limitation, not something to
  work around.
- The script can only tell "contents changed, version didn't" from git
  history - it can't tell a real feature addition from a typo fix in a
  comment. Because the CI check enforces this as a merge gate with no
  trivial-diff exception, apply judgment (step 4) only to size the bump,
  never to skip it.
- When running this as part of `docs/RELEASE-OPS.md` Step 0, open a
  version-bump PR per that document's "fix it now" guidance for anything
  flagged.
