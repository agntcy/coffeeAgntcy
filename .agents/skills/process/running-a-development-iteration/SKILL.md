---
name: running-a-development-iteration
description: >-
  Sequences a substantial change through the ideate/design/implement/
  review/document loop, checkpointing with self-review after every step
  and looping back when one fails. Use when starting or continuing a
  substantial change (the same threshold plan-with-openspec uses).
---

# Running a development iteration

## What this skill does

Sequences and checkpoints the five-step loop
[`.agents/rules/process/development-iteration-loop.md`](../../../rules/process/development-iteration-loop.md)
requires for a substantial change. It delegates every step's actual
content to the rule/skill that already owns it - this skill only decides
what runs next and when to loop back.

## Workflow

```
- [ ] 1. Ideate - if the idea isn't concrete yet, work it through the
        openspec-explore skill until it is.
- [ ] 2. Design - invoke the openspec-propose skill (proposal, design,
        spec delta, tasks).
- [ ] 3. Review the design - before treating design as done, check it
        against self-review-after-change's five checks (mainly
        "requirements" and "common practices" apply pre-code; give
        "repo consistency"/"rule compliance"/"general integrity" a first
        pass here too). Note anything documentation-relevant that
        surfaces, as a running note in the proposal/design text - don't
        wait until step 6 to start tracking it. If review finds a
        problem, fix it and re-review before continuing (loop back to 1
        or 2 as needed).
- [ ] 4. Implement - invoke the openspec-apply-change skill, working
        through tasks.md. Add automated tests for each code change in the
        same task, unless infeasible (judgment call - see the rule).
        Keep appending documentation-relevant notes as they surface.
- [ ] 5. Review the implementation - run self-review-after-change's full
        five checks against the change as it now stands, plus
        pre-finalize-checks' applicable automated checks. If review finds
        a problem, loop back to whichever step owns it (1, 2, or 4),
        fix it, and re-review before continuing.
- [ ] 6. Document - run keep-docs-consistent's full documentation-surface
        sweep, reconciling it against the notes accumulated since step 1
        - not reconstructing from scratch. Review this step too: if it
        surfaces a problem, loop back the same way as any other step.
- [ ] 7. Once the PR merges, invoke the openspec-archive-change skill.
```

## Notes

- This skill sequences and checkpoints only - it never restates what
  `openspec-explore`, `openspec-propose`, `openspec-apply-change`,
  `self-review-after-change`, `keep-docs-consistent`, or
  `openspec-archive-change` themselves require. Read each for its own
  content.
- The loop-back clause is not optional under time pressure: a review
  finding at any step, including the last one, sends the change back to
  fix the step that owns it, then re-reviews before continuing.
- "Documentation notes start at step 1" has no separate file or format -
  for an OpenSpec-tracked change, the proposal/design text itself is
  where these notes live, since both already get written and revised
  starting at the design step, and ideate's own exploration can note
  documentation implications inline before a proposal even exists.
- See [`.agents/rules/process/development-iteration-loop.md`](../../../rules/process/development-iteration-loop.md)
  for the underlying rule, and
  [`.agents/rules/process/plan-with-openspec.md`](../../../rules/process/plan-with-openspec.md)
  for the substantial-change threshold this skill's trigger reuses.
