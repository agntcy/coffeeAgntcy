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
| `scripts/**` (including `scripts/lib/`) | `task shell:lint` |
| `.github/workflows/**` | `task workflows:lint` and `task workflows:check-permissions` |
| A `uses:`/`FROM`/`image:` reference (workflow, Dockerfile, compose file) | `task pins:check` |
| Any prose you wrote (docs, comments, this list included) | `task dashes:check` - see `.agents/rules/no-em-en-dashes.md` |
| Unsure, or several of the above | `task check:all` (runs all five, never fails fast, reports which passed/failed) |

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
  [`.agents/rules/self-review-after-change.md`](self-review-after-change.md)
  for that judgment-level review, which this rule complements rather than
  replaces.
- A failing check means fix the change, not the check - see
  `.agents/skills/linting-shell-scripts/SKILL.md`,
  `.agents/skills/linting-github-workflows/SKILL.md`,
  `.agents/skills/checking-pinned-references/SKILL.md`,
  `.agents/skills/checking-workflow-permissions/SKILL.md`, and
  `.agents/skills/checking-dashes/SKILL.md` for how to read and fix
  specific failures.
- If a check doesn't apply (e.g. a pure-documentation change that doesn't
  touch `scripts/` or `.github/workflows/` and adds no third-party
  reference), skip it - don't run `task check:all` reflexively when a more
  targeted check (or none) clearly covers what changed.
