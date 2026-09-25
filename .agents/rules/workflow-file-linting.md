---
name: workflow-file-linting
description: >-
  Every file under .github/workflows/ must pass actionlint (schema,
  syntax, structure, and shellcheck findings in `run:` scripts) before
  being considered finished. Apply whenever writing or editing a workflow
  file. Checked by `task workflows:lint` (scripts/lint_workflows.bash),
  which is also the exact command the "Validate" step in
  .github/workflows/ci-gate.yaml runs.
---

# Workflow file linting

## Rule

Every file under `.github/workflows/` must pass **actionlint**
(<https://github.com/rhysd/actionlint>): schema/syntax/structure
validation, plus shellcheck run against every `run:` script embedded in
the file. Run `task workflows:lint` before treating any workflow file
change as finished, and fix everything it reports.

A shellcheck finding inside a `run:` script that's a genuine false
positive (e.g. a variable only read through indirect expansion, which
shellcheck can't trace) gets a targeted `# shellcheck disable=SCxxxx`
comment with a reason next to the line it applies to - the same practice
[`.agents/rules/shell-script-linting.md`](shell-script-linting.md)
describes for standalone scripts - rather than being left failing or
suppressed repo-wide.

## Why

A workflow file is YAML plus embedded shell, so it can be broken two
different ways at once: a malformed trigger/permission/matrix that GitHub
silently ignores or rejects at parse time, and a quoting/word-splitting bug
in a `run:` block that only surfaces the next time that code path
executes. actionlint catches both classes before merge instead of during a
live run.

## How to apply

- After writing or editing any file under `.github/workflows/`, run `task
  workflows:lint` (wraps
  [`scripts/lint_workflows.bash`](../../scripts/lint_workflows.bash), see
  [Taskfile.yaml](../../Taskfile.yaml)) and fix every finding it reports.
- Install locally: `task setup` (or `./scripts/setup.sh`) bootstraps
  actionlint, pinned to the version in
  [scripts/lib/versions.sh](../../scripts/lib/versions.sh), into
  `.tools/bin/` - no global install needed. Run `source scripts/env.sh` to
  put it on `PATH`.
- The "Validate" step in
  [`.github/workflows/ci-gate.yaml`](../../.github/workflows/ci-gate.yaml)
  runs this exact command on every push and pull request - a failing
  validation there means some workflow file in the diff needs fixing
  before merging (see that workflow's own "Wait"/"Summarize" steps for how
  the overall gate decision is made).
- See the `linting-github-workflows` skill for the full workflow.
