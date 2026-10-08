# Proposal

## Why

Helm charts aren't tagged in git - a chart's `Chart.yaml` `version:` field
is the only thing that identifies a published chart, so content that
changed without a version bump is invisible to anything downstream
(`helm upgrade`, another repo pinning a version, the `helm-push.yaml` CI
job, which only catches it at push-to-main time by rejecting a reused
version). `chore/add-helm-version-check` added a guard for this, but its
comparison window was scoped to `<last-release-tag>..HEAD` - an artifact
of wanting a small, fast check, not a reflection of the actual rule. The
real invariant ("a chart's version was bumped at or after its own last
real content change") has nothing to do with git tags: a chart that drifted
out of sync *before* the last release tag, and was never caught because
this check didn't exist yet, would stay invisible forever under a
tag-scoped design, since the check can never look further back than the
tag. This proposal replaces the tag-scoped window with an unbounded,
per-chart history walk, and builds the guard as this repo's standard
five-layer operation (script/task/skill/CI/rule) from the start.

## What Changes

- **Drop the tag/base-ref concept entirely.** For each `Chart.yaml` found
  in the repo, walk that chart's *entire* git history (no lower bound) to
  find the newest commit touching its contents (including `Chart.yaml`
  itself - `appVersion`/`dependencies`/etc. count) versus the newest
  commit that changed its own top-level `version:` line, and flag the
  chart if the former isn't covered by (isn't an ancestor of, or equal
  to) the latter.
- **No CLI arguments at all** - `task helm:check-versions` and the check
  it runs in CI always check as of `HEAD`, with nothing to default or
  override. (An earlier draft kept an optional `[<end-ref>]` for auditing
  an older ref; dropped since nothing calls it that way today and it adds
  a knob without a using it.)
- **`docs/RELEASE-OPS.md` Step 0 simplifies**: since the check has no
  release-tag lookup left to explain, Step 0 becomes "run `task
  helm:check-versions`" - the manual per-chart audit steps that used to
  walk a human through finding `LAST_RELEASE_TAG` and diffing against it
  are removed as redundant with what the automated check now always does.
- **State the known limitation explicitly, rather than silently**: `git
  log -- <chart-dir>` does not follow directory renames, so a chart
  directory renamed at some point in its history can under-report body
  changes from before the rename. This applies to both the old and new
  design equally (not a regression), but the new design's docs/rule call
  it out as a stated non-goal instead of leaving it implicit.
- **Full five-layer pipeline**: `scripts/checks/check_helm_chart_versions.bash`,
  a `helm:check-versions` Taskfile task, a `checking-helm-chart-version-bumps`
  skill, `task check:all`/`checks.yaml` CI enforcement (needs
  `fetch-depth: 0` on checkout to walk full chart history, not just a
  shallow recent slice), and a `helm-chart-version-bump` rule - all
  indexed in `AGENTS.md`.

## Capabilities

### New Capabilities

- `helm-chart-version-guard`: the requirement that a Helm chart's
  `Chart.yaml` `version:` field is bumped at or after that chart's own
  last real content change, checked across each chart's whole history
  (not scoped to any release tag), plus the script/task/skill/CI/rule
  layers that enforce and document it.

### Modified Capabilities

None - `repo-tooling`'s "every standing check runs together" requirement
already generalized to "any further check added to
`scripts/checks/check_all.bash`'s parallel list" during earlier work, so
it doesn't need a further edit to remain accurate once
`helm:check-versions` joins that list.

## Impact

- New check script, one new Taskfile task, one new skill, one new rule,
  `AGENTS.md` index updates, `scripts/checks/check_all.bash` gains one
  more parallel check.
- `checks.yaml`'s checkout step gains `fetch-depth: 0` (full history,
  needed to walk each chart's complete history rather than a shallow
  recent slice).
- `docs/RELEASE-OPS.md` Step 0 and `CONTRIBUTING.md`'s Helm-chart
  paragraph simplify to match the argument-free check.
- No existing chart's `Chart.yaml` changes; this only adds a check.
