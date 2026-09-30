---
name: pre-finalize-checks
description: >-
  Before considering work in this repo finished (and before pushing/opening
  a PR), run every check that applies to what changed. Not a git hook -
  something an agent runs proactively as its own last step.
---

# Pre-finalize checks

## Rule

Before treating a change in this repo as done - and always before pushing
or opening a PR - run whichever of these apply to what changed:

| If the change touches... | Run |
|---|---|
| `scripts/**` (including `scripts/lib/`) | `task shell:lint`, `task tests:bash`, and `task tests:coverage` |
| `.github/workflows/**` | `task workflows:lint` and `task workflows:check-permissions` |
| A `uses:`/`FROM`/`image:` reference (workflow, Dockerfile, compose file) | `task pins:check` |
| A file inside a Helm chart directory (`deployment/helm/<chart>/`) | `task helm:check-versions` - see `.agents/rules/quality/helm-chart-version-bump.md` |
| Any prose you wrote (docs, comments, this list included) | `task dashes:check` - see `.agents/rules/always-apply/no-em-en-dashes.md` |
| A new or changed `.agents/skills/*/SKILL.md`, or `repo-operation-pipeline.md`'s "Known exceptions" list | `task pipeline:check-exceptions` |
| A moved, renamed, or removed file, or an edited markdown link | `task links:check` |
| Unsure, or several of the above | `task check:all` (runs all ten, never fails fast, reports which passed/failed) |

This is deliberately **not** a pre-push git hook - nothing in this repo
installs one, and none should be added without the user asking for it. It's
a step an agent takes on its own initiative, the same way a careful
contributor would run tests before opening a PR.

## Why

CI (`checks.yaml`, `ci-gate.yaml`) enforces the same checks anyway, but
finding out from a failed CI run costs a round-trip; running `task
check:all` locally first catches the same problem immediately, before
anyone else sees it.

## How to apply

- Run the checks *after* the substantive change is otherwise complete, as
  the last step, not as a substitute for understanding whether the change
  itself is correct - see
  [`.agents/rules/always-apply/self-review-after-change.md`](self-review-after-change.md)
  for that judgment-level review, which this rule complements rather than
  replaces.
- A failing check means fix the change, not the check - see
  `.agents/skills/quality-checks/auditing-pipeline-exceptions/SKILL.md`,
  `.agents/skills/quality-checks/checking-dashes/SKILL.md`,
  `.agents/skills/quality-checks/checking-helm-chart-version-bumps/SKILL.md`,
  `.agents/skills/quality-checks/checking-markdown-links/SKILL.md`,
  `.agents/skills/quality-checks/checking-pinned-references/SKILL.md`,
  `.agents/skills/quality-checks/checking-workflow-permissions/SKILL.md`,
  `.agents/skills/quality-checks/linting-github-workflows/SKILL.md`,
  `.agents/skills/quality-checks/linting-shell-scripts/SKILL.md`, and
  `.agents/skills/quality-checks/testing-bash-scripts/SKILL.md` for how to
  read and fix specific failures.
- If a check doesn't apply (e.g. a pure-documentation change that doesn't
  touch `scripts/` or `.github/workflows/` and adds no third-party
  reference), skip it - don't run `task check:all` reflexively when a more
  targeted check (or none) clearly covers what changed.
