---
name: checking-helm-chart-version-bumps
description: >-
  Checks whether Helm charts under
  coffeeAGNTCY/coffee_agents/{corto,lungo}/deployment/helm/*/ that changed
  contents since a given base ref also had their Chart.yaml `version:`
  bumped, and bumps any that didn't. Use when editing files inside a Helm
  chart directory, before finishing such a change, when asked to check or
  audit Helm chart versions, or when performing docs/RELEASE-OPS.md Step 0
  before a release.
---

# Checking Helm chart version bumps

## What this skill does

Runs `task helm:check-versions -- <base-ref>` (defined in
[Taskfile.yaml](../../../Taskfile.yaml), wrapping
[scripts/check_helm_chart_versions.bash](../../../scripts/check_helm_chart_versions.bash))
to find every Helm chart whose contents changed since a base ref but whose
`Chart.yaml` `version:` didn't follow, then bumps each flagged chart by
ordinary semver judgment. This automates
[docs/RELEASE-OPS.md](../../../docs/RELEASE-OPS.md) Step 0 across all
charts at once instead of its manual per-chart snippet, and is the same
entry point the `helm-chart-versions` CI job uses. See
[.agents/rules/helm-chart-version-bump.md](../../rules/helm-chart-version-bump.md)
for the underlying rule.

## Workflow

```
- [ ] 1. Pick a base ref: the last release tag (git tag --list --sort=-creatordate
        | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' | head -n1), or whatever ref the
        user names (e.g. "since 0.3.0")
- [ ] 2. Run: task helm:check-versions -- <base-ref>
- [ ] 3. For each flagged chart, read what changed: git diff <base-ref> -- <chart-dir>
- [ ] 4. Every flagged chart needs a bump - the `helm-chart-versions` CI job
        is a merge gate with no trivial-diff exception, so even a pure
        comment/whitespace-only diff still needs (at least) a patch bump
- [ ] 5. Pick the bump level per ordinary semver:
        - patch: backward-compatible fix, internal tweak
        - minor: new value/template/feature, still backward compatible
        - major: breaking change to the chart's values.yaml interface or
          resource shape
- [ ] 6. Edit the flagged chart's Chart.yaml `version:` field (and any
        umbrella Chart.yaml dependency pin that references it)
- [ ] 7. Re-run task helm:check-versions -- <base-ref> to confirm every
        flagged chart is now clean
```

## Notes

- Charts are versioned independently - one chart's content change never
  requires bumping a sibling chart's version, even under the same umbrella
  repo.
- `appVersion` tracks the application image version, not the chart
  content - only bump it if the chart's default image tag/reference
  actually changed. Don't conflate it with `version:`.
- A chart with no prior release at the base ref has nothing to compare
  against; the script skips it, and its starting version is the author's
  call.
- The script can only tell "contents changed, version didn't" from git
  history - it can't tell a real feature addition from a typo fix in a
  comment. Because the CI job enforces this as a merge gate with no
  trivial-diff exception, apply judgment (step 5) only to size the bump,
  never to skip it.
- When running this as part of `docs/RELEASE-OPS.md` Step 0, use the last
  release tag as `<base-ref>` and `main` as the (default) end ref, and open
  a version-bump PR per that document's Step 0.3 for anything flagged.
