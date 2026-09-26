# Proposal

## Why

`.agents/rules/` (15 files) and `.agents/skills/` (13 hand-authored
directories, plus 6 CLI-generated `openspec-*` ones) are already flat
directories that `AGENTS.md`'s own tables group into named sections for
scannability. `.agents/rules/formatting/organize-large-collections.md` already
requires exactly this: "splitting `.agents/skills/` or `.agents/rules/`
into subdirectories by concern once either grows past a size where a flat
listing stops being scannable ... reusing whatever section names
`AGENTS.md`'s tables already grouped things under." Both have passed that
point - this proposal is applying that already-standing rule to the file
system, not inventing a new convention. `scripts/` (14 top-level files,
plus the `ci-gate/`/`lib/` subdirectories already carved out this way)
gets the same treatment, using the grouping the user separately asked for
earlier and deferred to this effort (mirroring the "one collective
directory per concern" pattern from the stashed OASF records work).

## What Changes

- Move `.agents/rules/*.md` into category subdirectories matching
  `AGENTS.md`'s existing "Rules" sections: `meta/`, `process/`,
  `always-apply/`, `quality/`, `formatting/`.
- Move `.agents/skills/*` (the 13 hand-authored ones) into category
  subdirectories matching `AGENTS.md`'s existing "Skills" sections:
  `domain-lungo/`, `repo-tooling/`, `quality-checks/`. The 6
  `openspec-*` skills stay flat at `.agents/skills/openspec-*/` -
  **BREAKING for that plan if reversed later**: they're written and
  overwritten by `openspec update`/`openspec init` at that fixed path,
  not hand-organized, so moving them would just have the next
  `openspec update` recreate flat copies alongside the moved ones.
- Move `scripts/*.bash` into `scripts/checks/` (every `check_*.bash`,
  `fix_dashes.bash`, and `find_strings.bash`, which the check/fix scripts
  call as a sibling) and `scripts/lint/` (`lint_shell.bash`,
  `lint_workflows.bash`). `scripts/setup.sh` and `scripts/env.sh` stay at
  `scripts/` - they're the bootstrap entry points a human/CI runs before
  any category exists, not members of a category (same "bootstrap
  predates the pipeline" exception `repo-operation-pipeline.md` already
  carves out for them). `scripts/ci-gate/` and `scripts/lib/` are
  unchanged - already organized this way.
- Update every cross-link and relative path this ripples into:
  `Taskfile.yaml`'s `cmds:`, each moved script's own
  `$SCRIPT_DIR/..`-based `REPO_ROOT` resolution (now one level deeper for
  the ones moving into `checks/`/`lint/`), every rule-to-rule and
  skill-to-rule markdown link, `AGENTS.md`'s tables, `.github/workflows/`
  prose, and the path strings baked into `repo-tooling-foundations`'
  and `repo-operation-governance`'s own (not yet archived) spec/design
  files, which assert several of these exact old paths.
- **No new capability, no behavior change**: `skip_specs: true` - this
  relocates files and fixes references so nothing points at a stale
  path; it doesn't change what any check, task, or skill does. `Taskfile.yaml`
  itself stays a single flat file (see design.md) - only the file-system
  trees move.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None (no `openspec/specs/` capability exists yet for any of this - both
`repo-tooling-foundations` and `repo-operation-governance` are still
unarchived, in-flight changes, not landed specs). Their own path
references are corrected in place as part of this change, the same way
an earlier correction fixed their stale "ci-gate.yaml Validate step"
references - see design.md.

## Impact

- Every file under `.agents/rules/`, `.agents/skills/` (except
  `openspec-*`), and `scripts/` (except `setup.sh`/`env.sh`/`ci-gate/`/
  `lib/`) moves to a new path.
- `AGENTS.md`, `Taskfile.yaml`, `.github/workflows/README.md`, and the
  two other open changes' artifacts get their path references updated.
- No workflow YAML changes: `checks.yaml`/`ci-gate.yaml` invoke checks
  via `task <name>`, not raw script paths (except `setup.sh`/`env.sh`/
  `ci-gate/*.sh`, none of which move).
