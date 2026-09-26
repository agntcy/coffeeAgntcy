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
- Changing `checks.yaml`'s intentional duplication of `workflows:lint`
  with `ci-gate.yaml`'s own Validate step - already a deliberate decision
  (see `checks.yaml`'s own header comment), unrelated to this change.

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

**The extraction changes only the Wait and Summarize steps; Validate
stays as a direct `task workflows:lint` call inline in the workflow.**
Validate is already a single `task` invocation with no bash logic of its
own to extract - there is nothing there that benefits from a script
file the way ~160 lines of polling/table-building logic does.

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
  flow instead of starting from nothing. Not something to fix, just worth
  naming so this change isn't mistaken for having caught a design issue
  before the fact when it mostly didn't need to.

## Migration Plan

`ci-gate.yaml`'s Wait/Summarize steps are replaced with `task` calls in
the same commit as the two new scripts and Taskfile tasks - no phased
rollout; the next push/PR after merge exercises the new path directly.
Rollback is a plain `git revert`. No other file changes behavior, so
there is nothing else to migrate.
