# Proposal

## Why

`.agents/rules/repo-operation-pipeline.md` (the five-layer script/task/
skill/CI/rule pattern) and the skills/rules built to support it
(`add-repo-operation`, `manage-repo-tooling`, `setup-repo-tooling`,
`pinned-tool-versions`, `pre-finalize-checks`) exist only as prose and
code, with no OpenSpec capability of their own - the same gap
`repo-tooling-foundations` (a separate, not-yet-archived change) already
closed for the standing checks built *on* this pattern. This proposal
documents the governance layer itself, and closes one real gap found
while reviewing it: the pipeline rule's "Known exceptions" list (which
rules are allowed to have no script/task/skill/CI layer) is unenforced
prose - nothing catches a listed rule quietly growing a skill later
without being promoted out of the list.

Two other questionable choices came up while reviewing this area:

- `ci-gate.yaml`'s own direct `task workflows:lint` call looked redundant
  with `checks.yaml` also running it via `task check:all` - it wasn't
  merely redundant, but it also wasn't right to leave as-is: `checks.yaml`
  only triggered on PRs targeting `main`, narrower than `ci-gate.yaml`'s
  own triggers (any PR, plus tag pushes), so dropping the duplicate call
  outright would have silently skipped workflow-file validation on a PR
  against any other branch, or on a tag push. Rather than document the
  duplication as load-bearing, `repo-tooling-foundations` (a separate,
  not-yet-archived change - amended after this exact discussion) closes
  the actual gap: `checks.yaml`'s triggers are broadened to match
  `ci-gate.yaml`'s, and `ci-gate.yaml` becomes a pure collector with no
  check logic of its own. See that change's `ci-gate` spec and
  `design.md` for the full resolution - this proposal doesn't restate it.
- `task setup` installs all six pinned tools unconditionally
  (~331MB, `node`+`openspec` alone ~215MB of it), even for a task that
  needs none of them. Keeping this eager and monolithic was a deliberate
  choice (see `design.md`), not an oversight.

## What Changes

- **Document, no behavior change**: `.agents/rules/repo-operation-pipeline.md`
  itself, `.agents/rules/pinned-tool-versions.md`,
  `.agents/rules/pre-finalize-checks.md`, and the
  `add-repo-operation`/`manage-repo-tooling`/`setup-repo-tooling` skills.
- **Document, no behavior change**: the eager-toolchain-install decision
  above - already true today, now written down as a deliberate decision
  rather than left for someone to "clean up" later under a mistaken
  assumption it's accidental. (The `ci-gate.yaml`/`checks.yaml`
  trigger-scope fix is real behavior change, but lives in
  `repo-tooling-foundations`, not here - see above.)
- **ADDED**: a self-audit check for the pipeline rule's "Known
  exceptions" list - for each rule listed as a pure judgment-call
  exception (no script/task/skill/CI layer at all), confirms no skill
  under `.agents/skills/` references it. A rule that's grown a skill
  without being promoted out of the exception list means the list is
  now lying about that rule's actual status.

## Capabilities

### New Capabilities

- `repo-operation-governance`: the five-layer operation pipeline as a
  documented, audited convention - its "Known exceptions" list and the
  self-audit that keeps it honest, the three tooling-management skills
  (`setup-repo-tooling`, `manage-repo-tooling`, `add-repo-operation`),
  `pinned-tool-versions`' single-source-of-truth guarantee, and
  `pre-finalize-checks`' change-to-check mapping. Complements (does not
  restate) `repo-tooling-foundations`' `repo-tooling` capability, which
  covers the standing checks and toolchain bootstrap this pattern
  produces.

### Modified Capabilities

_None - `repo-tooling-foundations` has not been archived yet (per
`.agents/rules/plan-with-openspec.md`, archiving happens after a
change's PR merges; nothing here has merged), so there is no main spec
under `openspec/specs/` yet to target with a delta. This capability is
additive against an empty `openspec/specs/` tree, same as
`repo-tooling-foundations` was._

## Impact

- `scripts/check_pipeline_exceptions.bash` (new): the self-audit script.
- `Taskfile.yaml`: new `pipeline:check-exceptions` task.
- `.agents/skills/auditing-pipeline-exceptions/SKILL.md` (new).
- `scripts/check_all.bash`: adds the new check to the parallel list, so
  `task check:all` and `checks.yaml` pick it up.
- `AGENTS.md`: indexes the new skill and (if a new rule file is added
  for this specific check rather than folding into
  `repo-operation-pipeline.md` itself - see `design.md`) the new rule.
- No change to any file `repo-tooling-foundations` already touches or
  specs (`ci-gate.yaml`, `scripts/ci-gate/*`, the five standing checks,
  `checks.yaml`).
