---
name: development-iteration-loop
description: >-
  A substantial change (the same threshold plan-with-openspec uses)
  proceeds through five steps in order - ideate, design, implement,
  review, document - with review run after every step, looping back to
  fix a step whose review finds a problem, and documentation-relevant
  notes tracked from the ideate step onward rather than reconstructed at
  the end. Apply when starting or continuing a substantial change.
---

# Development iteration loop

## Rule

A substantial change - the same threshold
[`plan-with-openspec`](plan-with-openspec.md) already uses: a new
tool/script/CI check, a schema or repo-wide convention change, or anything
spanning more than a small, self-contained diff - proceeds through five
steps, in order, as a loop rather than a single pass:

1. **Ideate** - work the idea through `openspec-explore` until it's
   concrete enough to propose.
2. **Design** - `openspec-propose` (proposal, design, spec delta, tasks).
3. **Implement** - `openspec-apply-change`, working through `tasks.md`. A
   code change made in this step gets automated tests added in the same
   step, unless doing so is infeasible - a judgment call, the same bar
   [`bash-script-testing`](../quality/bash-script-testing.md) already sets
   within its own domain, generalized here to any code change.
4. **Review** - [`self-review-after-change`](../always-apply/self-review-after-change.md)'s
   five checks, run after **every** step above, not only once at the end.
5. **Document** - [`keep-docs-consistent`](../always-apply/keep-docs-consistent.md)'s
   documentation-surface sweep, reconciling notes that started
   accumulating at the ideate step (in the proposal/design text itself)
   rather than being reconstructed cold at the end.

**Loop-back:** a review that finds a problem at any step sends the change
back to the step that owns the problem - or an earlier step it depends on
- to fix it, then that step's review runs again before continuing. This
can repeat; it's a loop, not a single pass.

A small, self-contained change (a bug fix, a small doc update, a single
self-contained script) keeps the normal PR flow instead - the same
carve-out `plan-with-openspec` already makes.

## Why

`plan-with-openspec` (ideate/design/implement), `self-review-after-change`
(review), and `keep-docs-consistent` (document) already cover one step
each, but nothing ties them into one sequence today. In practice this
means review only happens once, at the very end - after a bad design is
already implemented against, instead of before - and documentation gets
reconstructed from scratch at the end instead of tracked as it surfaces.
Naming the loop, requiring review after every step with explicit
loop-back, and requiring documentation notes to start at ideation closes
both gaps without duplicating what the three existing rules already say.

## How to apply

- This rule adds sequencing, continuity, and loop-back on top of the
  three rules above - it doesn't restate their content. Read each of them
  for what its own step actually requires.
- As an agent, use the
  [`running-a-development-iteration`](../../skills/process/running-a-development-iteration/SKILL.md)
  skill for the concrete checklist that sequences these five steps and
  their checkpoints.
- "Automated tests unless infeasible" is a judgment call, same as
  `bash-script-testing`'s own "genuine reason" bar - infeasible means
  genuinely impractical to test (e.g. no code changed at all, as in a
  pure documentation change), not merely inconvenient.
- If a review at the document step (the last one) still finds a problem,
  loop back the same way as any other step - reaching the last step
  doesn't exempt it from the loop-back clause.
