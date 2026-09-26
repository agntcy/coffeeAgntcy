# Design

## Context

The tooling this change documents was built by porting patterns from
`cisco-eti/ioc-app-mas-patterns` (a sibling repo sharing the same
underlying convention) across several sessions: repo-local toolchain
bootstrap, the five-layer operation pipeline, the standing checks, and
`checks.yaml`'s consolidation of what used to be two separate workflows.
See `proposal.md` - Why for why this is being spec'd now rather than
when it was built. `ci-gate.yaml` itself predates all of that work and
was not part of the port; comparing it against the reference repo's own
(newer) fork of the same script surfaced the sibling-run deadlock this
change also fixes.

## Goals / Non-Goals

**Goals:**
- Every requirement in both new specs SHALL match this repo's actual,
  already-running behavior, except for the one named bug fix - this is a
  brownfield spec, not aspirational.
- The `ci-gate:wait`/`ci-gate:summarize` extraction SHALL be directly
  runnable outside a live Actions run (with fake/canned inputs), the way
  every other script in `scripts/` already is - inline `run:` YAML
  cannot be exercised outside CI at all.

**Non-Goals:**
- Reorganizing `.agents/rules/`/`.agents/skills/` into the reference
  repo's nested category subdirectories
  (`.agents/rules/{always-apply,formatting,meta,quality}/`,
  `.agents/skills/{repo-tooling,quality-checks}/`). This repo deliberately
  kept both flat and grouped `AGENTS.md`'s index into labeled sections
  instead, when `openspec` was added and the Skills/Rules tables first
  grew past a flat list's scannability - a decision already made, not
  revisited here. Reconsider only if the flat layout itself becomes hard
  to scan, per `.agents/rules/organize-large-collections.md`.
- Porting any other reference-repo divergence not identified in
  `proposal.md` - Why (e.g. their `pins:check`/`workflows:check-permissions`
  scripts differ from ours in minor ways not affecting behavior this spec
  covers; not audited line-by-line here).

## Decisions

**Two capabilities, not one.** `repo-tooling` (the toolchain, the
pipeline pattern, the five standing checks, `checks.yaml`) and `ci-gate`
(the required-status-check workflow) are split because they're testable
independently and have different change cadences: `repo-tooling` grows
whenever a new check is added (following `add-repo-operation`);
`ci-gate`'s own state machine (poll/settle/timeout/decide) is a
self-contained piece of logic that doesn't grow the same way. Bundling
both extraction-worthy pieces into one 'misc tooling' capability would
make future changes to either one touch a spec section irrelevant to
what actually changed.

**The wait/summarize scripts take their CI context from environment
variables with local-friendly defaults, exactly like the reference
repo's fork.** `wait-for-sibling-runs.sh` reads `GITHUB_REPOSITORY`,
`GITHUB_RUN_ID`, `HEAD_SHA`, and a `gh`-authenticated environment - all
either set automatically by Actions or passed by the calling workflow
step - with `SETTLE_DELAY_SECONDS`/`POLL_INTERVAL_SECONDS`/
`OVERALL_TIMEOUT_SECONDS`/`CONSECUTIVE_CLEAN_POLLS_REQUIRED` defaulting
via `: "${VAR:=default}"` rather than requiring the workflow's `env:`
block to supply them. `summarize-ci-gate.sh` writes to
`$GITHUB_STEP_SUMMARY` when set, else stdout, and only `cat`s the
summary file back into the log when a real step-summary file exists (to
avoid double-printing when there isn't one). This is what makes both
scripts runnable by hand with fabricated inputs, not only inside a real
Actions run.

**Fix the sibling-exclusion bug by filtering on `workflow_id`, resolved
fresh from the same API response every poll - not by hardcoding CI
Gate's own workflow ID.** The current code excludes only
`select(.id != $self)`. The fix adds `own_workflow_id` (the
`workflow_id` of the run matching `$self` in the same payload) and
excludes any run sharing it: `select($ownwf == null or .workflow_id !=
$ownwf)`. Resolving it from the response rather than hardcoding a
workflow ID avoids a second, separately-drifting source of truth for
"which workflow is this" - the same commit's API response already
contains the answer. `summarize-ci-gate.sh` applies the identical
exclusion when building its table, for the same reason the reference
repo's own summarize script does: without it, a still-`in_progress` twin
CI Gate run (excluded from *waiting on*, but not yet excluded from
*judging*) would be counted as a failing sibling and fail the summary
outright.

**CI Gate's own Validate step is removed entirely, not merely
extracted - `checks.yaml` becomes the sole owner of workflow-file
validation, with its triggers broadened to match CI Gate's own.**
Reviewing why CI Gate ran `task workflows:lint` directly at all (rather
than only via `checks.yaml`) surfaced the real reason: `checks.yaml`'s
triggers were narrower (`pull_request: branches: [main]` only) than CI
Gate's (`pull_request: {}`, any branch, plus tag pushes) - dropping CI
Gate's own call without fixing that gap would have silently skipped
validation on an off-`main` PR or a tag push. The fix addresses the gap
directly instead of preserving the duplication around it: `checks.yaml`
now triggers on the exact same event set as `ci-gate.yaml`, which makes
`checks.yaml` unconditionally one of CI Gate's sibling runs, on every
commit CI Gate itself ever runs on. With that guarantee in place, CI
Gate genuinely doesn't need to run any check of its own - it becomes a
pure collector: checkout, wait, summarize, nothing else. Alternative
considered (the original resolution before this review): keep both,
document the duplication as load-bearing; superseded because the actual
fix (align the triggers) is no harder than documenting around the gap,
and leaves CI Gate simpler besides.

**CI Gate invokes `scripts/ci-gate/wait-for-sibling-runs.sh` and
`scripts/ci-gate/summarize-ci-gate.sh` directly, not via `task`, and no
longer bootstraps the toolchain at all.** With the Validate step gone,
nothing in CI Gate's job needs `shellcheck`/`shfmt`/`actionlint`/`node`/
`openspec` - only `bash`, `jq`, and `gh`, all already on a GitHub-hosted
runner. Running `./scripts/setup.sh` just to get the `task` binary onto
`PATH`, in order to run two scripts that need none of what it installs,
would be paying the full ~331MB eager-install cost (see
`repo-operation-governance`'s proposal.md) for zero benefit in this one
job. `task ci-gate:wait`/`task ci-gate:summarize` remain the documented
local/agent entry points to the same scripts, per
`.agents/rules/repo-operation-pipeline.md`; CI Gate itself just calls
the scripts underneath them directly.

## Risks / Trade-offs

- [Behavior drift during extraction] -> the ported bash could
  subtly diverge from the current inline version beyond the one intended
  fix. Mitigated by diffing the extracted scripts against the current
  inline steps line-by-line during implementation, and by testing both
  scripts locally with fabricated `runs.json`-shaped input before
  relying on a live CI run to validate them.
- [Both specs describe existing behavior but were written after the
  fact, not before implementation] -> the usual "spec first" value (catch
  a bad approach before the diff exists) doesn't apply retroactively for
  most of this change; the value here is purely making the *next* change
  to this surface go through the normal propose -> spec -> implement
  flow instead of starting from nothing. This is exactly what happened
  with the Validate-step redesign above: reviewing the already-documented
  "kept as-is" duplication out loud surfaced that it was actually a gap
  worth closing, not a decision worth keeping - caught by writing it down
  and discussing it, one step later than ideal but still before either
  spec was archived.
- [Broadening `checks.yaml`'s triggers increases CI minutes] -> it now
  runs on every pull request (any target branch) and every tag push, not
  only PRs/pushes targeting `main`. Not mitigated: this is the direct
  cost of closing the coverage gap, and is small next to the risk it
  replaces (workflow-file changes going unvalidated on non-`main` PRs).

## Migration Plan

`ci-gate.yaml`'s Wait/Summarize steps call
`scripts/ci-gate/wait-for-sibling-runs.sh`/`summarize-ci-gate.sh`
directly (no `task`, no toolchain bootstrap); its Validate step is
removed; `checks.yaml`'s triggers are broadened to match - all in the
same commit as the two new scripts and Taskfile tasks. No phased
rollout; the next push/PR after merge exercises the new path directly.
Rollback is a plain `git revert`. No other file changes behavior, so
there is nothing else to migrate.
