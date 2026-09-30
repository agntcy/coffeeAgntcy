# Spec Delta

## Purpose

Defines this repo's own development tooling: a repo-local pinned
toolchain bootstrap, the five-layer script/task/skill/CI/rule pattern
every repo operation follows, the standing checks built on that pattern,
and the CI workflow that runs them all together.

## ADDED Requirements

### Requirement: A repo-local toolchain installs without touching the global system
`task setup` (equivalently `./scripts/setup.sh`) SHALL install `task`,
`actionlint`, `shellcheck`, `shfmt`, `node`, and `openspec` into this
repo's own `.tools/` directory, and SHALL NOT modify the invoking user's
global `PATH`, shell profile, or home directory. `source scripts/env.sh`
SHALL put `.tools/bin` and `.tools/node/bin` on `PATH` for the invoking
shell session only.

#### Scenario: Fresh clone with no toolchain installed
- **WHEN** `task setup` is run in a clone with no `.tools/` directory
- **THEN** every tool listed above is installed under `.tools/`, and no
  file outside this repo's working tree is modified

### Requirement: Every pinned tool's version is checked for drift, not just presence
`scripts/lib/versions.sh` SHALL be the single place a tool's version is
pinned. `task setup` SHALL compare each tool's *installed* version
against its pin and reinstall on any mismatch - a tool already present at
the wrong version SHALL NOT be treated as satisfying the pin merely
because a binary exists at its expected path.

#### Scenario: A pin is bumped after the tool is already installed
- **WHEN** a tool's pinned version in `scripts/lib/versions.sh` is
  changed and `task setup` is run again
- **THEN** that tool is reinstalled at the newly pinned version, even
  though a binary from the old version was already present

### Requirement: Every repo operation follows the same five-layer pattern
An operation added to this repo (a check, a validation, a piece of
tooling) SHALL be built as: a script under `scripts/` (or
`scripts/lib/` for a shared helper), a Taskfile task wrapping exactly
that script, a skill under `.agents/skills/` pointing an agent at the
task, CI enforcement running the same task, and a rule under
`.agents/rules/` documenting the convention and cross-linking the other
four layers. A documented exception applies when an operation is a
judgment-call convention no script can reliably check, is CI-only
orchestration with no meaningful local invocation, is the bootstrap
tooling itself, or is a purely generative one-shot action with nothing
standing left to check once it runs - each such exception SHALL be
named explicitly, not left as a silent gap.

#### Scenario: A new check is added
- **WHEN** a new standing check is added to this repo
- **THEN** it has a script, a Taskfile task wrapping only that script, a
  skill, CI enforcement (via `scripts/check_all.bash`'s parallel list,
  or its own workflow only if its execution model genuinely differs),
  and a rule documenting it - unless it falls under a named exception

### Requirement: Dashes are checked and fixable
`task dashes:check` SHALL scan the repo for an em dash (U+2014) or en
dash (U+2013) and report every hit by file and line, without modifying
any file. `task dashes:fix` SHALL replace every such hit with a plain
ASCII hyphen in place.

#### Scenario: A dash is present
- **WHEN** `task dashes:check` is run against a repo containing an em
  dash or en dash anywhere in a tracked or untracked, non-ignored file
- **THEN** it reports that file and line, and exits non-zero

### Requirement: Shell scripts are linted and format-checked
`task shell:lint` SHALL run `shellcheck` and `shfmt` (pinned to `-i 4
-ci`) against every `.sh`/`.bash` file in the repo and report every
finding without modifying any file. `task shell:fmt` SHALL rewrite every
such file's formatting in place with `shfmt`, without addressing
`shellcheck` findings.

#### Scenario: A script has a shellcheck finding or formatting drift
- **WHEN** `task shell:lint` is run against a repo containing a
  shellcheck finding or a file not matching the pinned `shfmt` style
- **THEN** it reports the finding or diff, and exits non-zero

### Requirement: Workflow files are linted
`task workflows:lint` SHALL run `actionlint` against every file under
`.github/workflows/` and report every finding.

#### Scenario: A workflow file has a schema, syntax, or embedded-shellcheck finding
- **WHEN** `task workflows:lint` is run against a repo containing such a
  finding in any `.github/workflows/*.y*ml` file
- **THEN** it reports the finding and exits non-zero

### Requirement: Workflow file permissions are checked for least privilege
`task workflows:check-permissions` SHALL flag any `.github/workflows/`
file that grants `write-all` (workflow- or job-level) or leaves
permissions completely undeclared.

#### Scenario: A workflow grants write-all or declares no permissions
- **WHEN** `task workflows:check-permissions` is run against a repo
  containing such a file
- **THEN** it reports that file and exits non-zero

### Requirement: Third-party references are checked for immutable pinning
`task pins:check` SHALL flag any `uses:` reference in
`.github/workflows/*.y*ml`, `FROM` instruction in a Dockerfile, or
`image:` field in a compose file that targets a third-party
action/reusable-workflow/image by a mutable tag or branch instead of an
immutable commit SHA or digest, unless that line carries a `#
pin-exempt: <reason>` comment.

#### Scenario: A third-party reference is unpinned
- **WHEN** `task pins:check` is run against a repo containing such a
  reference with no `pin-exempt` comment
- **THEN** it reports that reference by file and line and exits non-zero

### Requirement: Every standing check runs together, in parallel, without failing fast
`task check:all` SHALL run `dashes:check`, `shell:lint`,
`workflows:lint`, `workflows:check-permissions`, and `pins:check` in
parallel, SHALL run every one of them to completion regardless of any
other's outcome, and SHALL end its output with a summary line reporting
pass/fail for each. It SHALL exit non-zero if any of them failed.

#### Scenario: One check fails, others pass
- **WHEN** `task check:all` is run and exactly one of the five checks
  would fail on its own
- **THEN** all five still run to completion, the summary reports each
  one's own pass/fail, and the overall command exits non-zero

### Requirement: CI runs every check after a single toolchain bootstrap
The `Checks` GitHub Actions workflow (`checks.yaml`) SHALL trigger on
every pull request targeting `main`, every push to `main`, and manual
`workflow_dispatch`. It SHALL bootstrap the toolchain once
(`./scripts/setup.sh`) and then run `task check:all`, rather than each
check bootstrapping its own runner.

#### Scenario: A pull request is opened against main
- **WHEN** a pull request targeting `main` is opened or updated
- **THEN** the `Checks` workflow runs, bootstrapping the toolchain once
  and then running every check in `task check:all`
