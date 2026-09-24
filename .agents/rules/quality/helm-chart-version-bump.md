---
name: helm-chart-version-bump
description: >-
  Any change to a Helm chart's contents (anything under a chart's own
  `deployment/helm/<chart>/` directory, including `Chart.yaml` itself) must
  bump that chart's `version:` field in `Chart.yaml` in the same change.
  Apply whenever editing files inside a Helm chart directory. Checked by
  `task helm:check-versions` (scripts/checks/check_helm_chart_versions.bash)
  against that chart's whole history, not just since the last release, and
  runs as part of `task check:all` in .github/workflows/checks.yaml.
---

# Helm chart version bump

## Rule

Every Helm chart under `coffeeAGNTCY/coffee_agents/{corto,lungo}/deployment/helm/*/`
is packaged and published independently, keyed by its own `Chart.yaml`
`version:` field - see `CONTRIBUTING.md` and
[`docs/RELEASE-OPS.md`](../../../docs/RELEASE-OPS.md) Step 0, which already
state this rule and its automated audit. Whenever a change touches any
file inside one of these chart directories - `templates/`, `values.yaml`,
`Chart.yaml` itself (dependencies, `appVersion`), or anything else in the
chart - bump that chart's own `version:` field in the same change. A chart
that didn't change keeps its version untouched; charts are versioned
independently of each other and of the umbrella repo/CHANGELOG version.

Use ordinary semver judgment for the bump itself (patch for a
backward-compatible fix or internal tweak, minor for a new
value/template/feature that's still backward compatible, major for a
breaking change to the chart's values.yaml interface or resource shape) -
this rule only requires *that* a bump happens, not which segment. There is
no trivial-diff exception: even a pure comment/whitespace-only change to a
chart still needs (at least) a patch bump, since `task helm:check-versions`
enforces this as a CI merge gate with no such carve-out.

## Why

Helm charts aren't tagged in git - a chart consumer (the `helm-push.yaml`
CI packaging job, `helm upgrade`, another repo pinning a chart version) has
no way to see that a chart's content changed unless `Chart.yaml`'s
`version:` says so. Content changed with no version bump is invisible to
anything downstream, and `helm-push.yaml`'s `check-push-target-existence`
guard only catches it at push-to-main time by rejecting a reused version -
it doesn't stop the unbumped PR from merging, which is why this rule also
has its own CI gate (see below) rather than relying only on that guard.

The check compares each chart's own *entire* git history, not a window
scoped to the last release tag - a violation older than the last release,
never caught because this check didn't exist yet, would otherwise stay
invisible forever, since a tag-scoped window can never look further back
than the tag. The rule itself ("bumped at or after the chart's own last
real content change") has nothing to do with tags in the first place.

## How to apply

- After editing any file inside a chart directory, check whether that
  chart's `Chart.yaml` `version:` changed too, before treating the change
  as finished.
- Run `task helm:check-versions` (no arguments; wraps
  [scripts/checks/check_helm_chart_versions.bash](../../../scripts/checks/check_helm_chart_versions.bash),
  see [Taskfile.yaml](../../../Taskfile.yaml)) to check every chart in the
  repo at once - it flags any chart whose contents changed, anywhere in
  its history, without a later version bump covering that change. See the
  `checking-helm-chart-version-bumps` skill for the full workflow,
  including how to pick the bump level.
- A chart's very first commit (which both adds it and sets its starting
  version) is never flagged - there's nothing earlier to compare against.
- **Known limitation**: the check doesn't follow a chart directory's
  renames (`git log`'s own limitation, not a design choice) - a rename
  can under-report content changes from before it. Stated here explicitly
  rather than left as a silent gap.
- `task check:all` in
  [`.github/workflows/checks.yaml`](../../../.github/workflows/checks.yaml)
  runs `helm:check-versions` alongside every other standing check on every
  push to `main` and every pull request - a red run means some chart needs
  a bump before merging. It's also the tool for the release-time audit in
  `docs/RELEASE-OPS.md` Step 0.
