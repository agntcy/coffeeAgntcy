---
name: repo-operation-pipeline
description: >-
  Every repository operation - a check, a validation, a piece of tooling -
  should be built through the same five-layer pipeline: a script, a
  Taskfile task, a skill, CI enforcement (for checks/invariants), and a
  rule documenting it. Apply when adding or changing any operation, or
  auditing whether an existing one is complete. See the
  `add-repo-operation` skill for the step-by-step checklist.
---

# Repository operation pipeline

## Rule

Any operation added to this repo - a validation, a check, a piece of build
automation - should be implemented through the same five layers, in this
order, each calling the one before it:

1. **Script** (`scripts/<name>.bash`, or `scripts/lib/*.sh` for a shared
   helper sourced by other scripts) - the actual implementation.
2. **Taskfile task** (`Taskfile.yaml`) - wraps exactly one script; this is
   what a human runs by hand.
3. **Skill** (`.agents/skills/<name>/SKILL.md`) - points an agent at the
   task, not the underlying script; this is what an agent invokes.
4. **CI enforcement** - the same task runs on every push/PR. For every
   check, including one specifically about workflow files, this means
   adding it to
   [`scripts/check_all.bash`](../../scripts/check_all.bash)'s parallel
   list, so `task check:all` in
   [`.github/workflows/checks.yaml`](../../.github/workflows/checks.yaml)
   picks it up with no other file needing to change.
   [`ci-gate.yaml`](../../.github/workflows/ci-gate.yaml) runs no check
   of its own - it only waits for and summarizes sibling runs (including
   `checks.yaml`), so it never needs a new check folded into it. Only
   give a check its own workflow file if it has a genuinely different
   execution model (see "Known exceptions" below). Applies to
   checks/invariants (something that should always hold); it doesn't
   apply to a purely generative, one-shot action, which has nothing
   standing left to check once it's run.
5. **Rule** (`.agents/rules/<name>.md`) - documents the convention or
   expectation itself, and cross-links the other four layers. Indexed from
   `AGENTS.md`.

Shell script linting is the reference example - every layer present, each
one calling the one before it:
[`scripts/lint_shell.bash`](../../scripts/lint_shell.bash) ->
`shell:lint`/`shell:fmt` in [`Taskfile.yaml`](../../Taskfile.yaml) ->
[`.agents/skills/linting-shell-scripts/SKILL.md`](../skills/linting-shell-scripts/SKILL.md)
-> one of the parallel checks
[`scripts/check_all.bash`](../../scripts/check_all.bash) runs, via `task
check:all` in
[`.github/workflows/checks.yaml`](../../.github/workflows/checks.yaml) ->
[`.agents/rules/shell-script-linting.md`](shell-script-linting.md).

A check's CI layer doesn't need its own workflow file -
[`checks.yaml`](../../.github/workflows/checks.yaml) bootstraps the
toolchain once and then runs every such check in parallel via `task
check:all` (see [`scripts/check_all.bash`](../../scripts/check_all.bash)),
instead of each one re-bootstrapping on its own runner. Add a new check by
adding it to `check_all.bash`'s list, not by creating a new workflow file.

## Why

An operation that only exists in one place - a script nobody knows to run,
a CI check with no local equivalent, a convention stated once in prose with
nothing enforcing it - gets skipped, drifts, or has to be rediscovered
every time someone needs it. Building every operation through the same
five layers means a human always has a `task` command for it, an agent
always has a skill pointing at that same command, CI never checks
something that can't also be run locally, and the convention behind it is
always written down somewhere agents actually read (`AGENTS.md` and
`.agents/rules/`).

## How to apply

When adding a new operation, see the `add-repo-operation` skill for the
step-by-step checklist.

When auditing an existing operation, check for the same five layers; a
missing one is a gap to fill, not something to leave implicit. `AGENTS.md`'s
Skills and Rules tables, plus `Taskfile.yaml` and `.github/workflows/`, are
the places to check against.

## Known exceptions

- **Purely manual/visual conventions**, and judgment calls that can't be
  reliably automated without false positives (e.g.
  [`.agents/rules/alphabetize-entity-lists.md`](alphabetize-entity-lists.md),
  [`.agents/rules/file-tree-comment-alignment.md`](file-tree-comment-alignment.md),
  [`.agents/rules/keep-docs-consistent.md`](keep-docs-consistent.md),
  [`.agents/rules/organize-large-collections.md`](organize-large-collections.md),
  [`.agents/rules/plan-with-openspec.md`](plan-with-openspec.md),
  [`.agents/rules/pre-finalize-checks.md`](pre-finalize-checks.md),
  [`.agents/rules/self-review-after-change.md`](self-review-after-change.md)),
  are legitimate rule-only exceptions - they say so explicitly, rather than
  silently lacking a script/task/skill/CI layer. This list is itself
  audited: `task pipeline:check-exceptions`
  ([`scripts/check_pipeline_exceptions.bash`](../../scripts/check_pipeline_exceptions.bash),
  see the `auditing-pipeline-exceptions` skill) fails, naming the rule,
  if any of them has since gained a skill of its own without being
  promoted out of this list.
- **CI-only orchestration steps** with no meaningful local invocation (the
  "Wait" and "Summarize" steps in
  [`ci-gate.yaml`](../../.github/workflows/ci-gate.yaml)) don't need a
  skill - they only make sense inside a live CI run against real Actions
  API state, and `ci-gate.yaml` is already the rule-layer documentation for
  what they do.
- **Bootstrap tooling itself** (`scripts/setup.sh` / `task setup` / the
  `setup-repo-tooling` skill) is the one part of the pipeline that predates
  having a pipeline to follow - it's a documented exception in that skill,
  not an oversight.
- **Purely generative, one-shot actions** (updating, adding, or removing a
  pinned tool version - see
  [`.agents/rules/pinned-tool-versions.md`](pinned-tool-versions.md)) don't
  need a CI workflow, for the reason given in layer 4 above; they still
  get script, task, and skill layers.
- **A genuinely different execution model** still warrants its own
  workflow file instead of joining an existing job -
  [`ci-gate.yaml`](../../.github/workflows/ci-gate.yaml) is the example: it
  polls the Actions API for sibling workflow runs and waits on them, which
  only makes sense as its own workflow.
