# Tasks

## 1. Write the rule

- [ ] 1.1 Write `.agents/rules/process/development-iteration-loop.md`:
      frontmatter (name, description ending in the same "apply when
      starting or continuing a substantial change" trigger language as
      `plan-with-openspec`), and a body naming the five steps
      (ideate/design/implement/review/document), mapping each to its
      existing mechanism, stating the tests-in-implement requirement, the
      continuous-review clause, and the loop-back clause; verify it reads
      as a cross-linking layer, not a restatement, by confirming it never
      duplicates a full sentence from `plan-with-openspec.md`,
      `self-review-after-change.md`, or `keep-docs-consistent.md`

## 2. Write the skill

- [ ] 2.1 Write
      `.agents/skills/process/running-a-development-iteration/SKILL.md`:
      frontmatter (name `running-a-development-iteration`, description
      matching the rule's trigger), and a checklist (one item per step)
      naming which existing skill/rule to invoke at each point, with the
      loop-back behavior spelled out as an explicit checklist item under
      the review step; verify by re-reading it against
      `.agents/skills/brainstorming` (not present in this repo - use
      `.agents/skills/quality-checks/testing-bash-scripts/SKILL.md`'s
      checklist shape instead as the in-repo precedent) for format
      consistency
- [ ] 2.2 Add a "Notes" section to the skill cross-linking every
      rule/skill it sequences, and stating explicitly that it sequences
      and checkpoints only

## 3. Cross-link the existing rules

- [ ] 3.1 Add a cross-link sentence to `plan-with-openspec.md` pointing at
      the new rule, noting that once a change clears the threshold, the
      new rule governs the sequencing loop around it
- [ ] 3.2 Add a cross-link sentence to `self-review-after-change.md`
      clarifying it's invoked at every step of the loop (per the new
      rule), not only as a single final pass
- [ ] 3.3 Add a cross-link sentence to `keep-docs-consistent.md` noting
      that for a change following the iteration loop, tracking what needs
      updating starts at ideation rather than being reconstructed cold at
      the end
- [ ] 3.4 Confirm none of these three edits change any existing
      requirement of those rules - cross-links and one clarifying
      sentence only

## 4. Update the index

- [ ] 4.1 Add a new "Process" skill group to `AGENTS.md`'s Skills section
      (paired with the existing "Process" rules group) listing the new
      skill
- [ ] 4.2 Add the new rule as a row in `AGENTS.md`'s existing "Process"
      rules table, alongside `plan-with-openspec`
- [ ] 4.3 Verify `AGENTS.md`'s tables list exactly what's on disk under
      `.agents/rules/process/` and `.agents/skills/process/` and nothing
      else

## 5. Verify

- [ ] 5.1 Run `task dashes:check` and `task links:check` against the new
      and edited files; confirm both pass clean
- [ ] 5.2 Run `openspec validate "development-iteration-loop" --strict`;
      confirm it passes
- [ ] 5.3 Apply `self-review-after-change` and `pre-finalize-checks` to
      this change itself (the fitting infeasible/judgment-call case from
      this change's own tests-in-implement requirement: no code exists
      here to cover with automated tests, only prose to get right by
      review)
