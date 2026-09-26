# Spec Delta

## Purpose

Defines this repo's governance layer for its own tooling: the five-layer
operation pipeline convention every check/tool follows, the audited list
of judgment-call exceptions to it, and the skills that guide adding a
new operation or managing the pinned toolchain. Complements the
`repo-tooling` capability (a separate, not-yet-archived change), which
covers the standing checks this pattern produces.

## ADDED Requirements

### Requirement: Every operation follows script -> task -> skill -> CI -> rule
An operation added to this repo (a check, a validation, a piece of
tooling) SHALL be built as a script, a Taskfile task wrapping exactly
that script, a skill pointing an agent at the task, CI enforcement
running the same task, and a rule documenting the convention and
cross-linking the other four layers - unless it falls under a named,
documented exception.

#### Scenario: A new check is added with no exception
- **WHEN** a new standing check is added with none of the documented
  exceptions applying to it
- **THEN** it has all five layers, each calling the one before it

### Requirement: The exception list is audited, not just asserted
Every rule listed as a "purely manual/visual convention" exception (no
script/task/skill/CI layer at all) SHALL have no skill under
`.agents/skills/` referencing it by filename. `task
pipeline:check-exceptions` SHALL check this for every rule in that list
and fail, naming the rule, if one now has such a skill.

#### Scenario: An exception-listed rule gains a skill without being promoted
- **WHEN** a rule listed as a rule-only exception has a skill under
  `.agents/skills/` that references it by filename
- **THEN** `task pipeline:check-exceptions` fails and names that rule

#### Scenario: Every exception-listed rule still has no skill
- **WHEN** none of the rule-only exception list's rules has a skill
  referencing it
- **THEN** `task pipeline:check-exceptions` passes

### Requirement: Bootstrapping is the one documented exception to the pipeline itself
`scripts/setup.sh` / `task setup` SHALL be invocable directly, without
going through a Taskfile task that itself requires `task` to already be
installed - this is the one part of the pipeline allowed to predate
having a pipeline to follow, and is a documented exception, not an
oversight.

#### Scenario: task is not yet installed
- **WHEN** `task` is not present on a fresh clone
- **THEN** `./scripts/setup.sh` still succeeds when run directly

### Requirement: Adding a new operation follows a documented checklist
The `add-repo-operation` skill SHALL guide adding a script, then a
Taskfile task wrapping only that script, then a skill, then CI
enforcement (added to `scripts/check_all.bash`'s parallel list unless
the operation's execution model genuinely differs), then a rule
cross-linking the other four - in that dependency order.

#### Scenario: A new operation is added following the skill
- **WHEN** a new operation is added by following the `add-repo-operation`
  skill's checklist
- **THEN** every layer exists before the operation is considered
  complete, in the order the checklist states

### Requirement: Managing pinned tool versions follows a documented workflow
The `manage-repo-tooling` skill SHALL guide updating a pinned version
(edit `scripts/lib/versions.sh`, then `task setup`, then confirm the
installed version, then re-run standing checks since a version bump can
shift lint/format output), introducing a new tool, and removing one -
as three distinct workflows, none of which requires a dedicated CI
check of its own.

#### Scenario: A pinned version is bumped
- **WHEN** a tool's pinned version in `scripts/lib/versions.sh` is
  bumped following the `manage-repo-tooling` skill
- **THEN** `task setup` reinstalls that tool at the new version and the
  standing checks are re-run to catch any output shift

### Requirement: scripts/lib/versions.sh is the single source of truth for pinned versions
No tool's version SHALL be hardcoded anywhere in this repo other than
`scripts/lib/versions.sh`.

#### Scenario: A tool's version is referenced
- **WHEN** any script, task, workflow, or doc needs to state a pinned
  tool's version
- **THEN** it reads or points at `scripts/lib/versions.sh` rather than
  stating a version number of its own

### Requirement: Pre-finalize checks map what changed to what to run
`.agents/rules/pre-finalize-checks.md` SHALL state, for each kind of
change (a script, a workflow file, a third-party reference, any prose),
which `task` command to run before treating that change as finished,
plus a catch-all (`task check:all`) for an unsure or multi-kind change.

#### Scenario: A change touches a script and a workflow file
- **WHEN** a change touches both a file under `scripts/` and a file
  under `.github/workflows/`
- **THEN** the mapping calls for both `task shell:lint` and `task
  workflows:lint` (or the catch-all `task check:all`) before the change
  is considered finished
