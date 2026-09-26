---
name: plan-with-openspec
description: >-
  Before writing code for a feature or substantial change (a new tool,
  script, or CI check; a schema or repo-wide convention change; anything
  spanning more than a small, self-contained diff), propose it with
  `openspec propose` and get the plan right before implementing. Archive it
  with `openspec archive` after the PR merges. A small, self-contained
  change keeps the normal PR flow instead. Apply when starting work that
  doesn't fit that flow.
---

# Plan with OpenSpec

## Rule

Before starting a feature or substantial change to this repo - a new
tool/script/CI check, a schema or repo-wide convention change, or anything
that spans more than a small, self-contained diff - run `openspec propose`
and get the resulting proposal, design, spec delta, and tasks list right
before writing any code. Implement against that plan (`openspec apply`, or
by hand following its `tasks.md`), then run the normal `task check:all` /
PR flow. Once the PR merges, run `openspec archive` so the change's
rationale and final spec delta land in `openspec/specs/` as the durable
record, instead of being buried in a merged PR's diff.

A routine, self-contained change (a bug fix, a small doc update, a single
new script that doesn't ripple elsewhere) keeps the normal PR flow -
that's already scoped enough on its own and doesn't need a separate
OpenSpec proposal on top of it.

## Why

A small change is self-contained: one diff, one review pass. A tooling or
convention change isn't - it ripples across scripts, skills, rules, docs,
and CI (see
[`.agents/rules/repo-operation-pipeline.md`](repo-operation-pipeline.md)),
and design mistakes caught after the diff is written cost far more to
unwind than mistakes caught in a plan. Proposing first means the reasoning
behind a substantial change is written down and reviewable before it's
irreversible, and stays discoverable afterward in `openspec/specs/` rather
than living only in a PR description.

## How to apply

- If unsure whether something counts as "substantial," err on proposing -
  an unused `openspec/changes/<name>/` costs little; a substantial change
  with no written plan costs a lot more to review or unwind.
- As an agent, reach for the generated `openspec-propose` /
  `openspec-explore` / `openspec-apply-change` / `openspec-update-change` /
  `openspec-archive-change` / `openspec-sync-specs` skills under
  `.agents/skills/` rather than typing the CLI subcommands named above
  directly - see the "OpenSpec workflow" note in `AGENTS.md`'s Skills
  table.
- `openspec` itself is part of this repo's normal local toolchain (`task
  setup` installs it, alongside a pinned Node.js it needs to run) - see
  the `manage-repo-tooling` / `setup-repo-tooling` skills if it's reported
  missing.
- This is a rule-only convention, one of the judgment-call exceptions
  [`.agents/rules/repo-operation-pipeline.md`](repo-operation-pipeline.md)
  already carves out: there's no way to script "was this proposed before
  it was coded."
- After `openspec init` or `openspec update` regenerates the
  `openspec-*` skill files under `.agents/skills/`, run `task dashes:fix`
  before committing - the CLI's own generated prose isn't written against
  this repo's [`no-em-en-dashes`](no-em-en-dashes.md) rule and can
  reintroduce an em dash or en dash.
