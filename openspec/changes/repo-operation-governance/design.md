# Design

## Context

See `proposal.md` - Why for the trigger-scope and eager-install findings,
and for why this is additive against an empty `openspec/specs/` tree
rather than a delta against `repo-tooling-foundations` (not yet
archived). `.agents/rules/repo-operation-pipeline.md`'s "Known
exceptions" section currently lists, under "purely manual/visual
conventions" with no script/task/skill/CI layer at all:
`alphabetize-entity-lists`, `file-tree-comment-alignment`,
`keep-docs-consistent`, `organize-large-collections`,
`plan-with-openspec`, `pre-finalize-checks`, `self-review-after-change`.
Every skill's `SKILL.md` already cross-links "the underlying rule" by
filename (e.g. `linting-shell-scripts/SKILL.md` names
`shell-script-linting.md`) - that existing convention is what the new
check reuses as its drift signal.

## Goals / Non-Goals

**Goals:**
- The new audit SHALL catch exactly one failure mode: a rule listed in
  the "purely manual/visual conventions" exception bucket that has since
  gained a skill referencing it (meaning it quietly got automation and
  the exception list is now wrong about it).

**Non-Goals:**
- Auditing the other four exception categories in
  `repo-operation-pipeline.md` (CI-only orchestration, bootstrap tooling
  itself, one-shot generative actions, genuinely-different execution
  model). Each asserts something structurally different (a missing
  skill only, a specific historical exemption, a missing CI layer only,
  a workflow-file-existence choice) that doesn't reduce to the same
  "does a skill reference this rule" check - automating all five well
  would need four different signals for four different assertions, for
  categories that change far less often than a new skill gets added.
  Revisit only if one of those categories actually drifts in practice.
- Changing the eager-install or ci-gate-duplication behavior - both
  reviewed and kept (see `proposal.md`).
- Reorganizing `.agents/rules/`/`.agents/skills/` or `scripts/` into
  nested category subdirectories - already out of scope per
  `repo-tooling-foundations`' own design.md, and the user has a separate
  planned effort for this (mentioned when that change was discussed).

## Decisions

**The audit's "rule" layer is `repo-operation-pipeline.md` itself,
updated in place - not a new standalone rule file.** The convention
being enforced ("the Known exceptions list stays accurate") is part of
what that rule already asserts about itself; a separate
`pipeline-exception-audit.md` rule would be a rule about a rule,
documenting the exact same list a second time with its own drift risk
between the two copies. Cross-linking the new script/task/skill from
within the existing "Known exceptions" section keeps one copy of the
list as the source of truth.

**The exception list is hardcoded in the script, not parsed from the
rule's markdown.** Extracting rule names from
`repo-operation-pipeline.md`'s prose (a markdown bullet list with
inline links) is fragile against reformatting that doesn't change
meaning. A hardcoded bash array with a comment pointing at the rule
section it must stay in sync with is the same pattern
`scripts/check_all.bash` already uses for its own check list, and
`scripts/lib/versions.sh` for pinned tool versions - this repo already
accepts "hardcoded list, comment says where its source of truth is"
over "parse the prose" elsewhere.

**Drift signal is "a skill's `SKILL.md` has a markdown link ending in
the rule's filename (`...<rule>.md)`) within a couple of lines before
the phrase 'underlying rule'", not just the filename appearing near that
phrase.** Went through two tightenings while actually building the
check, both caught by running it against the real repo before trusting
it: `add-repo-operation` already mentions `alphabetize-entity-lists.md`
and `pre-finalize-checks.md` in passing (telling agents to also apply
those rules while adding an operation) without being "the skill for"
either, so a bare "filename anywhere near the phrase" signal flagged
both as false positives immediately. Requiring the phrase within a fixed
line window of the filename wasn't enough either: this capability's own
`auditing-pipeline-exceptions` skill has to *explain* the mechanism,
which means using the trigger phrase and example rule names close
together in ordinary prose - exactly the false positive it exists to
avoid, on itself. What actually distinguishes a real cross-link is the
closing `)` of a markdown link: every genuine "underlying rule" skill
writes `[.agents/rules/<rule>.md](path/<rule>.md)` immediately before
the phrase, while prose that merely discusses a rule (in backticks, or a
bare filename) never produces that exact shape. Requiring it is what
finally caught the same thing a human reviewer would look for (whose
skill is this rule's own cross-link, not who else mentions it) without
tripping on this change's own documentation.

## Risks / Trade-offs

- [Hardcoded exception list drifts from the rule's prose] -> if a rule
  is added to or removed from `repo-operation-pipeline.md`'s exception
  bullet without updating the script's array, the audit checks a
  slightly stale list. Mitigated by a comment in the script pointing
  directly at the section to keep in sync, and by `task
  pipeline:check-exceptions` being cheap enough to remember alongside
  any edit to that section - not by parsing (see Decisions above).
- [False negative if a skill exists but doesn't name the rule by
  filename] -> the check would miss automation that exists but doesn't
  follow the filename cross-link convention. Not separately mitigated:
  every skill in this repo already follows that convention (verified
  during review), and a skill that doesn't would itself be a
  `self-review-after-change` finding independent of this check.

## Migration Plan

Purely additive: one new script, one new task, one new skill, one
cross-link edit to an existing rule, one line added to
`scripts/check_all.bash`'s list. No existing file's behavior changes.
Rollback is a plain `git revert`.
