# Proposal

## Why

This repo already has the pieces of a disciplined development iteration -
`plan-with-openspec` (ideate/design via `openspec propose`, implement via
`openspec apply`), `self-review-after-change` (review), and
`keep-docs-consistent` (document) - but nothing ties them into one named
sequence. In practice this means review only happens once, at the very
end, instead of catching a bad design before it's implemented against;
and documentation gets reconstructed from scratch at the end instead of
being tracked as it surfaces. Naming the loop explicitly, requiring
review after every step (not only the last), and requiring documentation
notes to start accumulating from the first step closes both gaps without
duplicating what the existing rules already say.

## What Changes

- **A new rule** (`.agents/rules/process/development-iteration-loop.md`):
  names the five-step loop - ideate, design, implement, review, document -
  maps each step to the existing mechanism that already covers it, and
  adds what's missing: review runs after *every* step, a failed review
  loops back to the step that owns the problem (or an earlier one) before
  continuing, and documentation-relevant notes start accumulating at the
  ideate step rather than being reconstructed cold at the end. Applies at
  the same threshold `plan-with-openspec` already uses; a small,
  self-contained change keeps the normal PR flow.
- **A new requirement folded into the implement step**: a code change made
  during implementation gets automated tests in the same step unless
  infeasible (a judgment call, the same bar `bash-script-testing` already
  sets for its own domain) - generalizing that existing precedent beyond
  bash scripts specifically.
- **A new skill** (`.agents/skills/process/running-a-development-iteration/SKILL.md`):
  the procedural checklist that actually sequences the loop - invoking
  `openspec-explore`, `openspec-propose`, `openspec-apply-change`,
  `self-review-after-change`, `keep-docs-consistent`, and
  `openspec-archive-change` at the right points, with the loop-back and
  continuous-review behavior spelled out as concrete steps. It sequences
  and checkpoints only; it doesn't restate any of those rules'/skills' own
  content.
- **Small cross-linking edits** to `plan-with-openspec.md`,
  `self-review-after-change.md`, and `keep-docs-consistent.md`: each gains
  a one- or two-sentence note and a link pointing at the new rule/skill,
  clarifying that they're invoked repeatedly within the loop rather than
  once.
- **`AGENTS.md`**: a new "Process" skill group (paired with the existing
  "Process" rules group) for the new skill; a new row in the existing
  "Process" rules table for the new rule.

## Capabilities

### New Capabilities

- `development-iteration-loop`: the requirement that a substantial change
  follows an explicit ideate/design/implement/review/document loop, with
  review run after every step (looping back on failure) and documentation
  notes tracked from the first step onward, plus the requirement that
  implementation includes automated tests unless infeasible.

### Modified Capabilities

None - `plan-with-openspec`, `self-review-after-change`, and
`keep-docs-consistent` aren't OpenSpec-tracked capabilities themselves
(they're rule-only conventions, same as noted in `plan-with-openspec.md`'s
own "How to apply" section), so cross-linking edits to their rule files
aren't a spec-level requirement change.

## Impact

- New rule file, new skill file, `AGENTS.md` index updates.
- Small edits to three existing rule files (cross-links only, no change to
  their own requirements).
- No code, no scripts, no CI changes - this is a process/documentation
  change.
