---
name: helm-chart-version-bump
description: >-
  Any change to a Helm chart's contents (anything under a chart's own
  `deployment/helm/<chart>/` directory, including `Chart.yaml` itself) must
  bump that chart's `version:` field in `Chart.yaml` in the same change.
  Apply whenever editing files inside a Helm chart directory. Checked by
  `task helm:check-versions -- <base-ref>` (scripts/check_helm_chart_versions.bash),
  which also runs as the `helm-chart-versions` job in
  .github/workflows/source-lint.yaml on push to main and on pull requests.
---

# Helm chart version bump

## Rule

Every Helm chart under `coffeeAGNTCY/coffee_agents/{corto,lungo}/deployment/helm/*/`
is packaged and published independently, keyed by its own `Chart.yaml`
`version:` field - see `CONTRIBUTING.md` and
[`docs/RELEASE-OPS.md`](../../docs/RELEASE-OPS.md) Step 0, which already
state this rule and its manual audit process. Whenever a change touches any
file inside one of these chart directories - `templates/`, `values.yaml`,
`Chart.yaml` itself (dependencies, `appVersion`), or anything else in the
chart - bump that chart's own `version:` field in the same change. A chart
that didn't change keeps its version untouched; charts are versioned
independently of each other and of the umbrella repo/CHANGELOG version.

Use ordinary semver judgment for the bump itself (patch for a
backward-compatible fix or internal tweak, minor for a new
value/template/feature that's still backward compatible, major for a
breaking change to the chart's values.yaml interface or resource shape) -
this rule only requires *that* a bump happens, not which segment.

## Why

Helm charts aren't tagged in git - a chart consumer (the `helm-push.yaml`
CI packaging job, `helm upgrade`, another repo pinning a chart version) has
no way to see that a chart's content changed unless `Chart.yaml`'s
`version:` says so. Content changed with no version bump is invisible to
anything downstream, and `helm-push.yaml`'s `check-push-target-existence`
guard only catches it at push-to-main time by rejecting a reused version -
it doesn't stop the unbumped PR from merging, which is why this rule also
has its own CI gate (see below) rather than relying only on that guard.

## How to apply

- After editing any file inside a chart directory, check whether that
  chart's `Chart.yaml` `version:` changed too, before treating the change
  as finished.
- Run `task helm:check-versions -- <base-ref>` (a previous release tag,
  e.g. the last `X.Y.Z` release tag; wraps
  [scripts/check_helm_chart_versions.bash](../../scripts/check_helm_chart_versions.bash),
  see [Taskfile.yaml](../../Taskfile.yaml)) to check every chart in the
  repo against that baseline at once - it flags any chart whose contents
  changed since `<base-ref>` without a later version bump. See the
  `checking-helm-chart-version-bumps` skill for the full workflow,
  including how to pick the bump level.
- A chart with no prior release at the base ref (new since then) has
  nothing to compare against - the script skips these; leave their version
  as whatever the author chose.
- The `helm-chart-versions` job in
  [`.github/workflows/source-lint.yaml`](../../.github/workflows/source-lint.yaml)
  runs the same check on every push to `main` and every pull request,
  comparing against the last non-`-dev` release tag - a red job means some
  chart in the diff needs a bump before merging. It's also the tool for the
  release-time audit in `docs/RELEASE-OPS.md` Step 0.
