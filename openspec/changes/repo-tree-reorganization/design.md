# Design

## Context

See `proposal.md` for the motivation - this is applying the already-standing
`organize-large-collections` rule to three flat trees that have grown past
scannable size, plus a previously-deferred `scripts/` grouping the user asked
for earlier in this effort. The target category names for `.agents/rules/`
and `.agents/skills/` are not new - they're derived from `AGENTS.md`'s
existing table section headers (three of five rule categories and both
skill categories below are exact matches; `quality`/`formatting` are
shortened from "Code/content quality"/"Formatting & organization
conventions" for the reason given below, and `AGENTS.md`'s own headers
are left as the friendlier prose they already were, not renamed to match):

- Rules: `meta/`, `process/`, `always-apply/`, `quality/`,
  `formatting/`
- Skills: `domain-lungo/`, `repo-tooling/`, `quality-checks/` (the
  `openspec-*` skills' own "OpenSpec workflow" section stays flat and
  excluded - see proposal.md)

`scripts/` has no such pre-existing section names to reuse (it was never
split in `AGENTS.md`), so this design has to pick category names for it from
scratch. `repo-tooling-foundations`' own `design.md` already named this
exact reorg as a **Non-Goal** when that change was written - "kept both
flat... a decision already made, not revisited here" - naming the
reference repo's own category names for illustration:
`.agents/rules/{always-apply,formatting,meta,quality}/`,
`.agents/skills/{repo-tooling,quality-checks}/`. This change supersedes
that Non-Goal (the flat layout did become hard to scan, which is exactly
the condition that Non-Goal named as the reason to reconsider) and reuses
those exact names rather than the `formatting-organization`/
`code-content-quality` names this change initially drafted, for
consistency with that already-documented reference convention; `process/`
is added as a fifth rule category beyond the reference repo's four
because this repo's OpenSpec workflow rule doesn't fit any of them.

## Goals / Non-Goals

**Goals:**
- Every moved file's new path is discoverable from `AGENTS.md`'s tables (kept
  in sync, not left stale) and every cross-link between rules, skills, and
  scripts is updated to match - no broken relative link, no script that
  silently starts resolving its own `REPO_ROOT` wrong.
- Both `repo-tooling-foundations` and `repo-operation-governance` (still
  open, all tasks checked, not yet archived) have their own spec/design
  files' path references corrected in the same change, so neither describes
  a path that no longer exists once this merges.

**Non-Goals:**
- Splitting `Taskfile.yaml` into per-category included files (see Decisions
  below) - task names stay a single flat file with colon-namespacing.
- Moving or reorganizing the 6 CLI-generated `openspec-*` skills - see
  proposal.md.
- Any change to what a check, task, or skill actually does - purely path
  relocation plus reference fixes.

## Decisions

**`scripts/` groups into `checks/` (every `check_*.bash`, plus
`fix_dashes.bash` and `find_strings.bash`) and `lint/`
(`lint_shell.bash`, `lint_workflows.bash`), not one directory per script or
a `fix/` directory of its own.** `fix_dashes.bash` is `check_dashes.bash`'s
auto-fix counterpart (same underlying `find_strings.bash` helper, same
concern - the dashes rule), so splitting it into its own single-file `fix/`
directory would be a category sized for one item with nothing else designed
to join it; grouping it with the checks it fixes is the more natural
boundary. `lint_shell.bash`/`lint_workflows.bash` are a distinct concern
(external linters over specific file types, not this repo's own
forbidden-string-style checks) and already read as a pair, so they get their
own `lint/` group rather than joining `checks/`.

**`Taskfile.yaml` stays one flat file - it does not gain a `checks/`,
`lint/`, etc. split via `includes:`.** At ~13 tasks it isn't past the point
`organize-large-collections` triggers at yet, and it already carries its own
namespacing (`dashes:`, `shell:`, `workflows:`, `pins:`, `pipeline:`,
`ci-gate:`) that gives the same "pick the right group, then scan that"
benefit a physical split would, at zero added indirection. Splitting it
now would be organizing for a size the file hasn't reached, not the size it
has.

**Scripts moving one directory deeper get their `REPO_ROOT` resolution
fixed from `$SCRIPT_DIR/..` to `$SCRIPT_DIR/../..`, not switched to
`git rev-parse --show-toplevel`.** `scripts/env.sh` already uses
`git rev-parse` because it's `source`d into an interactive shell where
`BASH_SOURCE`-based `SCRIPT_DIR` resolution is unreliable; every other
script here is always executed as a file (never sourced) so `SCRIPT_DIR`
resolution is reliable, and keeping the existing pattern (just fixing the
depth) is a smaller diff than introducing a second `REPO_ROOT` convention
for no behavioral gain.

**The two open, unarchived changes' own artifacts get their stale paths
fixed in place, not a new spec delta layered on top.** Same precedent as
the earlier `ci-gate.yaml` correction: since neither has been archived,
their proposal/design/spec/tasks files are still-being-refined planning
artifacts, not a landed contract - editing them directly to stay accurate
keeps one copy of the truth instead of a delta describing a change to a
spec that was never actually finalized at the old paths.

## Risks / Trade-offs

- [A missed cross-link reference leaves a rule/skill pointing at a path
  that no longer exists] -> mitigated by grepping the whole repo for every
  moved file's old path (not just the ones remembered as referencing it)
  before considering the move done, then re-running `task check:all` and
  `openspec validate --strict` on all three changes - the same verification
  discipline `organize-large-collections.md`'s own "How to apply" section
  already prescribes ("moving files is the easy part ... verify by actually
  running the moved thing afterward").
- [A relocated script's `REPO_ROOT` depth fix is missed, so it silently
  `cd`s to the wrong directory instead of erroring] -> mitigated by
  auditing every moved script for `SCRIPT_DIR`/`REPO_ROOT`/`cd` patterns
  before moving (done during this proposal - five scripts need the `../..`
  fix: `check_pinned_references.bash`, `check_workflow_permissions.bash`,
  `check_pipeline_exceptions.bash`, `lint_shell.bash`, `lint_workflows.bash`)
  and by actually running `task check:all` afterward rather than trusting
  the diff.
- [Category boundaries chosen here don't hold up as more scripts/skills/
  rules get added] -> acceptable: `organize-large-collections.md` already
  says design with room to grow, not permanence: a category can be split
  further or renamed later the same way this change is creating them now.

## Migration Plan

`git mv` each file/directory to its new path, fix the five scripts' `REPO_ROOT`
depth, fix `Taskfile.yaml`'s `cmds:` paths, fix every cross-link found by
grepping the repo for each old path (rules, skills, `AGENTS.md`,
`.github/workflows/README.md`, and the two sibling changes' own artifacts),
then run `task check:all`, `task dashes:check` (the generated `openspec-*`
skills are untouched, so no re-run of `openspec update` is needed), and
`openspec validate --strict` on `repo-tree-reorganization`,
`repo-tooling-foundations`, and `repo-operation-governance`. Rollback is a
plain `git revert` - nothing external depends on the old paths (no other
branch, no external doc links into this repo's `.agents/`/`scripts/` trees).
