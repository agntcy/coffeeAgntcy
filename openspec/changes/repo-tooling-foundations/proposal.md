# Proposal

## Why

Recent work (three merged commits: `chore(shell): add linters`,
`refactor(repo): upgrade tooling`, `chore(repo): add openspec`) brought
this repo's dev tooling up to the pattern established in
`cisco-eti/ioc-app-mas-patterns` - a repo-local pinned toolchain, a
five-layer script/task/skill/CI/rule pipeline, and a consolidated
parallel-checks workflow - but none of it has ever been written down as
an OpenSpec capability. It exists only as the code itself, `AGENTS.md`'s
index, and the `.agents/rules/*` prose. This proposal documents that
already-shipped surface as two capabilities (so future changes to it go
through the same propose -> spec -> implement flow as everything else),
and, while comparing against the reference repo's more evolved version of
the same lineage, found one concrete gap worth fixing in the same change
rather than filing separately: `ci-gate.yaml`'s sibling-run wait can
deadlock.

## What Changes

- **Document, no behavior change**: the repo-local toolchain bootstrap
  (`scripts/setup.sh`, `scripts/lib/*`, `scripts/env.sh`,
  `task setup`), the five-layer operation pipeline pattern itself
  (`.agents/rules/repo-operation-pipeline.md`), and every check built on
  it (`dashes`, `shell:lint`/`shell:fmt`, `workflows:lint`,
  `workflows:check-permissions`, `pins:check`), plus `task check:all` and
  the `checks.yaml` workflow that runs it in CI.
- **Document, no behavior change**: `ci-gate.yaml`'s existing role as the
  repo's single required status check - validate every workflow file,
  wait for every sibling workflow run on the same commit to finish, then
  summarize and decide pass/fail.
- **BUG FIX**: `ci-gate.yaml`'s wait step currently excludes only its own
  run ID from "runs to wait for," not every run of the CI Gate workflow
  itself. A non-squash merge to `main` can produce two CI Gate runs
  sharing one commit SHA (`pull_request`-triggered and
  `push`-triggered); each then waits on the other, deadlocking until the
  100-minute timeout. Fixed by excluding every run sharing CI Gate's own
  `workflow_id`, not just this run's own `id`.
- **Refactor, no observable behavior change beyond the fix above**:
  extract `ci-gate.yaml`'s inline "Wait" and "Summarize" bash (~160
  lines) into `scripts/ci-gate/wait-for-sibling-runs.sh` and
  `scripts/ci-gate/summarize-ci-gate.sh`, wired through `task
  ci-gate:wait` / `task ci-gate:summarize`, matching this repo's own
  `repo-operation-pipeline` rule (script -> task -> ...) instead of being
  the one workflow that doesn't follow it. Both scripts read their CI
  context from environment variables with local-friendly defaults, so
  they're directly runnable (with canned/fake inputs) outside a live
  Actions run - something inline `run:` YAML can never be.

## Capabilities

### New Capabilities

- `repo-tooling`: the repo-local pinned toolchain, the five-layer
  operation-pipeline pattern, every check built on it
  (dashes/shell/workflow-lint/pins/permissions), and the consolidated
  `checks.yaml` workflow that runs them all in CI.
- `ci-gate`: the required-status-check workflow - validate, wait for
  sibling runs, summarize and decide - including the sibling-run
  exclusion fix above.

### Modified Capabilities

_None - first OpenSpec capabilities for this surface; nothing under
`openspec/specs/` exists yet to modify._

## Impact

- `.github/workflows/ci-gate.yaml`: "Wait" and "Summarize" steps replaced
  with `task ci-gate:wait` / `task ci-gate:summarize` calls; behavior
  identical except for the deadlock fix.
- `scripts/ci-gate/wait-for-sibling-runs.sh`,
  `scripts/ci-gate/summarize-ci-gate.sh` (new).
- `Taskfile.yaml`: two new tasks, `ci-gate:wait` and `ci-gate:summarize`.
- No spec-relevant change to any other already-shipped file
  (`scripts/setup.sh`, `scripts/lib/*`, `scripts/check_*.bash`,
  `scripts/lint_*.bash`, `checks.yaml`, every `.agents/rules/*.md` this
  covers) - these are documented as-is.
- `ci-gate:wait`/`ci-gate:summarize` are CI-only orchestration with no
  meaningful local invocation, exactly like `.agents/rules/
  repo-operation-pipeline.md`'s existing exception for these two steps -
  they get script and task layers now, per this change, but still no
  skill, matching that documented exception.
