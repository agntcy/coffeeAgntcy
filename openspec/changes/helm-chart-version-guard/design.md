# Design

## Context

See proposal.md for motivation. Two things shape the approach:

- This repo's standard five-layer operation pipeline (script under
  `scripts/checks/` → Taskfile task → skill under `.agents/skills/` →
  CI enforcement via `scripts/checks/check_all.bash`'s parallel list,
  run by `checks.yaml`'s single toolchain-bootstrap job → rule under
  `.agents/rules/`, indexed in `AGENTS.md`) - see
  `.agents/rules/meta/repo-operation-pipeline.md`. Every standing check
  in this repo already follows it; this guard is built the same way from
  the start rather than bolted on afterward.
- `checks.yaml` runs every check from one shared checkout + bootstrap
  step, not a per-check job - adding a check that needs something the
  others don't (here, full git history) means changing that one shared
  checkout, not adding a second one.

## Goals / Non-Goals

**Goals:**
- Detect a chart whose contents changed without a version bump, no
  matter how far back in that chart's history the violation happened -
  not scoped to any release tag.
- Zero-argument invocation: `task helm:check-versions` always checks the
  current repository state as of `HEAD`, suitable for both a bare
  `task check:all` run and a human running it locally before opening a PR.
- Fit the existing five-layer pipeline exactly, with no special-casing.

**Non-Goals:**
- **Following directory renames.** `git log -- <chart-dir>` does not
  follow a chart directory that was renamed partway through its history,
  so a body change from before the rename can be under-reported. This is
  unchanged from the original (tag-scoped) design - neither design
  follows renames - but this design states it explicitly as a known
  limitation rather than leaving it implicit. If a chart is renamed, its
  post-rename history is what gets checked; nothing further is done
  about content that predates the rename under the old path.
- **Judging bump size.** The check only detects that a bump is missing,
  never whether it should be patch/minor/major - that judgment is the
  `checking-helm-chart-version-bumps` skill's job, applied by whoever
  fixes a flagged chart.
- **Auto-bumping** a flagged chart's version, or validating that a
  chart's version string is well-formed semver.
- **Retroactively backfilling** any chart alive today - see Migration
  Plan below; nothing needs it.

## Decisions

**Unbounded per-chart history walk, not a tag-scoped window.**
The original branch this supersedes compared `<last-release-tag>..HEAD`.
That window is an artifact of wanting a small, fast check, not the actual
rule ("version bumped at or after the chart's own last real content
change" - no mention of tags in that sentence). A violation older than
the last release tag, never caught because this check didn't exist yet,
would be permanently invisible under a tag-scoped design, since the
window can never look further back than the tag. Walking each chart's
whole history instead has no such blind spot, and costs nothing today:
probed against this repo's current 20 charts, all pass clean under the
unbounded comparison, so switching doesn't newly flag anything.
*Alternative considered*: keep the tag-scoped window for speed. Rejected
- `git log -1 -- <path>` finds the newest match without materializing
full history, so the unbounded version isn't meaningfully slower at this
repo's scale, and correctness matters more than a marginal speedup here.

**No CLI arguments at all - always `HEAD`, nothing else.**
An earlier draft kept an optional `[<end-ref>]` for auditing an older
ref. Dropped: nothing in this repo calls it that way, `task check:all`
only ever needs the current state, and a knob nothing exercises is a
knob nobody's tested. If auditing an older ref is ever actually needed,
it's a small, reversible addition to make then, informed by a real use
case instead of a guess now.

**Chart's own `Chart.yaml` counts as part of its "body," and `version:`
matching is anchored to the top-level field.**
The original branch (before its own follow-up "fix inconsistencies"
commit) excluded a chart's `Chart.yaml` from its own body comparison,
which meant an `appVersion`/`dependencies` edit inside `Chart.yaml` didn't
count as a content change needing a bump - and matched `version:` with
leading whitespace allowed (`^\s*version:`), which could mistake a nested
`dependencies: - version: ...` line for the chart's own top-level bump.
This design carries forward that branch's own fix: `Chart.yaml` is part
of the body, and the bump match is anchored (`^version:`, no leading
whitespace) so only the chart's own top-level field counts.

**`checks.yaml`'s single shared checkout gains `fetch-depth: 0`, rather
than a second checkout step scoped to just this check.**
The original branch's dedicated `source-lint.yaml` job used its own
`fetch-depth: 0` checkout, since it had its own job to put it in.
`checks.yaml` deliberately has only one checkout + bootstrap for every
check (see Context above) - splitting a second checkout out for one
check would undo that consolidation for no reason. Every check in that
job pays the fuller-clone cost, the same way other jobs in this repo
(e.g. `helm-push.yaml`) already do when they need tag/history depth.

## Risks / Trade-offs

- **[Risk]** A full, unbounded `git log` walk per chart could get slower
  as this repo's history grows. → **Mitigation**: `git log -1 -- <path>`
  stops at the first match, it doesn't walk and materialize entire
  history; revisit only if this becomes a measured bottleneck, not
  preemptively.
- **[Risk]** Introducing a stricter, tag-independent check could
  immediately flag charts that drifted out of sync long ago and were
  never caught. → **Mitigation**: verified empirically before finalizing
  this design - every existing chart in this repo already passes clean
  under the unbounded comparison, so (unlike `bash-script-testing`'s
  coverage audit, which needed a real backfill effort) there is nothing
  to backfill here.
- **[Risk]** `fetch-depth: 0` on `checks.yaml`'s shared checkout adds
  clone cost to every check in that job, not just this one. →
  **Mitigation**: accepted, consistent with this repo's "one shared
  bootstrap, not per-check" design; the added cost is the same full
  clone other jobs in this repo already pay for when they need history.
- **[Risk]** Directory renames under-report a chart's pre-rename history
  (see Non-Goals). → **Mitigation**: none automated; stated explicitly in
  the rule doc rather than left as a silent gap, so it's a known,
  documented limitation rather than a surprise.

## Migration Plan

No chart alive in this repo today needs a version bump under the new
comparison (verified directly - see Risks above), so this ships as a
plain addition, not a backfill:

1. Implement `scripts/checks/check_helm_chart_versions.bash` (unbounded,
   zero-argument).
2. Add the `helm:check-versions` Taskfile task.
3. Add the `checking-helm-chart-version-bumps` skill and the
   `helm-chart-version-bump` rule, indexed in `AGENTS.md`.
4. Wire into `scripts/checks/check_all.bash`'s parallel list.
5. Add `fetch-depth: 0` to `checks.yaml`'s checkout step.
6. Update `docs/RELEASE-OPS.md` Step 0 and `CONTRIBUTING.md`'s Helm-chart
   paragraph to match the argument-free check.
7. Run `task check:all` to confirm every existing chart passes clean
   before merging.

No rollback concerns beyond reverting the commit - this only adds a
check, it doesn't touch any chart's `Chart.yaml`.
