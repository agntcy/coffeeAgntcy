# Design

## Context

See `proposal.md` for the motivation. Three existing rules already cover
one step each of what this change names as a loop:
`plan-with-openspec` (ideate/design/implement, via the OpenSpec CLI and
its generated skills), `self-review-after-change` (review, today applied
once, at the end), and `keep-docs-consistent` (document, today
reconstructed at the end rather than tracked as it surfaces). This repo
also already pairs a declarative rule with a procedural skill for a
comparable convention (`bash-script-testing` + `testing-bash-scripts`),
which is the shape this design reuses.

## Goals / Non-Goals

**Goals:**
- Name the five-step loop (ideate, design, implement, review, document) in
  one place, without restating what the three existing rules already say.
- Make review a per-step gate with explicit loop-back, not a single final
  pass.
- Make documentation tracking start at ideation, not at the end.
- Generalize `bash-script-testing`'s "tests unless infeasible" bar to any
  code change made during implement.

**Non-Goals:**
- Replacing or restating `plan-with-openspec`, `self-review-after-change`,
  or `keep-docs-consistent` - this change only adds sequencing, loop-back,
  and continuity on top of them, via cross-links.
- A standalone general "write automated tests" rule - the tests-in-implement
  requirement lives inside this loop's own rule/skill content, since no
  other general testing rule exists to place it in instead.
- Automating any part of the loop mechanically (there's no script that can
  verify "review happened after every step" or "docs were tracked from
  step one") - this is a judgment-call convention, the same as
  `plan-with-openspec` already is for "was this proposed before it was
  coded."

## Decisions

**A rule + skill pair, not a rule alone or a skill alone.** A rule alone
(Approach B considered during design) would bury "review happens
continuously across all five steps" inside `plan-with-openspec`, a rule
nominally about when to use OpenSpec - a reader looking for the loop/review
framing would have to know to look there. A skill alone (Approach C
considered during design) would risk restating what `openspec-propose` /
`openspec-apply-change` / `self-review-after-change` / `keep-docs-consistent`
already do. Splitting them - as `bash-script-testing` (rule) +
`testing-bash-scripts` (skill) already do for a comparable case - lets the
rule stay the declarative "why/when" layer indexed in `AGENTS.md`'s Rules
table, and the skill stay a thin sequencing/checkpoint checklist (mirroring
`brainstorming`'s own todo-per-item shape) that delegates all step content
to what already exists.

**The skill only sequences and checkpoints; it never restates step
content.** Each checklist item names which existing rule/skill to invoke
(`openspec-explore`, `openspec-propose`, `openspec-apply-change`,
`self-review-after-change`, `keep-docs-consistent`,
`openspec-archive-change`) and where the loop-back and continuous-review
behavior fits in, rather than describing what any of those do internally.
This keeps the loop's own maintenance surface small - if
`self-review-after-change`'s five checks change, the skill doesn't need an
edit.

**Same substantial-change threshold as `plan-with-openspec`, not a new
one.** Introducing a second threshold definition would risk the two rules
disagreeing about when they apply. The loop rule explicitly cross-links
and reuses `plan-with-openspec`'s existing threshold language instead of
restating it.

**Tests-in-implement folded into this rule's content, not a new
standalone rule.** The repo has no general "write automated tests for
code changes" rule today - only `bash-script-testing`, scoped to bash
specifically. Rather than introduce a new, separately-indexed rule for a
one-sentence requirement, it's folded into the implement step's own
description here, citing `bash-script-testing` as the existing precedent
for the "unless infeasible" judgment-call bar.

## Risks / Trade-offs

- [Review-after-every-step and loop-back are judgment calls with no script
  to verify them, so they could be silently skipped under time pressure] ->
  same trust model this repo already extends to `plan-with-openspec`'s
  "was this proposed before it was coded" and `self-review-after-change`
  itself - both are unenforceable by automation and rely on the same
  discipline this change asks for one layer further in.
- [A rule/skill pair adds two new files for what could be read as a single
  three-sentence idea] -> deliberate, matching the existing
  `bash-script-testing`/`testing-bash-scripts` precedent; keeping the
  skill thin (sequencing only) keeps the actual maintenance surface small
  despite the file count.
- [The "document starts at step 1" requirement has no concrete artifact to
  point at - what does "tracking notes" mean mechanically?] -> for an
  OpenSpec-tracked change, the proposal/design text itself is that
  artifact (both already get written and revised starting at the design
  step, and ideate's own exploration can note documentation implications
  inline before a proposal even exists) - no new file or convention is
  needed to hold these notes.

## Migration Plan

Write `.agents/rules/process/development-iteration-loop.md` and
`.agents/skills/process/running-a-development-iteration/SKILL.md`; add
cross-linking edits (a sentence and a link each, no requirement changes)
to `plan-with-openspec.md`, `self-review-after-change.md`, and
`keep-docs-consistent.md`; add a new "Process" skill group and a new
"Process" rules-table row to `AGENTS.md`. Purely additive - no existing
rule's own requirements change, no code or CI is touched. Rollback is a
plain `git revert`.
