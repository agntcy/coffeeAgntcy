# repo-tooling Specification

## Purpose
Defines this repo's own development tooling: a repo-local pinned
toolchain bootstrap, the five-layer script/task/skill/CI/rule pattern
every repo operation follows, the standing checks built on that pattern,
and the CI workflow that runs them all together.

## Requirements

### Requirement: A repo-local toolchain installs without touching the global system
`task setup` (equivalently `./scripts/setup.sh`) SHALL install `task`,
`actionlint`, `shellcheck`, `shfmt`, `bats`, `node`, `openspec`, and
`renovate` into this repo's own `.tools/` directory, and SHALL NOT modify
the invoking user's global `PATH`, shell profile, or home directory.
`source scripts/env.sh` SHALL put `.tools/bin`, `.tools/node/bin`, and
`.tools/bats/bin` on `PATH` for the invoking shell session only.

#### Scenario: Fresh clone with no toolchain installed
- **WHEN** `task setup` is run in a clone with no `.tools/` directory
- **THEN** every tool listed above is installed under `.tools/`, and no
  file outside this repo's working tree is modified

### Requirement: Every pinned tool's version is checked for drift, not just presence
`scripts/lib/versions.sh` SHALL be the single place any tool's version is
pinned, including the npm-installed tools; any `package.json` used to
install them SHALL be generated from those pins, never separately
committed. `task setup` SHALL compare each tool's *installed* version against its pin and
reinstall on any mismatch - a tool already present at the wrong version
SHALL NOT be treated as satisfying the pin merely because a binary exists
at its expected path.

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
  skill, CI enforcement (via `scripts/checks/check_all.bash`'s parallel list,
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
`workflows:lint`, `workflows:check-permissions`, `pins:check`, and any
further check added to `scripts/checks/check_all.bash`'s parallel list
(e.g. `pipeline:check-exceptions`, added by the sibling
`repo-operation-governance` change) in parallel, SHALL run every one of
them to completion regardless of any other's outcome, and SHALL end its
output with a summary line reporting pass/fail for each. It SHALL exit
non-zero if any of them failed.

#### Scenario: One check fails, others pass
- **WHEN** `task check:all` is run and exactly one of its checks would
  fail on its own
- **THEN** all of them still run to completion, the summary reports each
  one's own pass/fail, and the overall command exits non-zero

### Requirement: CI runs every check after a single toolchain bootstrap
The `Checks` GitHub Actions workflow (`checks.yaml`) SHALL trigger on
every pull request (regardless of target branch), every push to `main`,
every push of a tag, and manual `workflow_dispatch` - the same event set
as `ci-gate.yaml` (see the `ci-gate` capability's own requirement on
this), so it is always among the sibling runs CI Gate collects. It
SHALL bootstrap the toolchain once (`./scripts/setup.sh`) and then run
`task check:all`, rather than each check bootstrapping its own runner.

#### Scenario: A pull request is opened against any branch
- **WHEN** a pull request is opened or updated, against any branch
- **THEN** the `Checks` workflow runs, bootstrapping the toolchain once
  and then running every check in `task check:all`

### Requirement: Downloaded tool archives are verified against pinned checksums
Every archive `task setup` downloads directly SHALL have its SHA-256
pinned, per exact download URL and for every supported OS and
architecture, in `scripts/lib/checksums.txt`. `task setup` SHALL verify
each download against that pin before unpacking or installing it, and
SHALL fail without installing anything from a download whose checksum
differs, or whose URL has no pinned checksum.

#### Scenario: A downloaded archive has been tampered with
- **WHEN** a tool's archive is served with content whose SHA-256 differs
  from the pinned one
- **THEN** `task setup` fails naming the URL and both digests, and that
  tool is not installed

#### Scenario: A pin is bumped without refreshing checksums
- **WHEN** a version in `scripts/lib/versions.sh` is changed but
  `scripts/lib/checksums.txt` still only pins the old URLs
- **THEN** `task setup` fails for that tool reporting that no checksum is
  pinned, before downloading anything

### Requirement: Checksum pins are regenerable and complete
`task tools:checksums` SHALL regenerate `scripts/lib/checksums.txt` so it
holds exactly one line per distinct download URL, for every directly
downloaded tool on every supported platform, at the currently pinned
versions. A unit test SHALL fail if the file pins any other set of URLs.

#### Scenario: Regenerating after a version bump
- **WHEN** `task tools:checksums` is run after bumping a version
- **THEN** the file holds lines for the new URLs and none for the old
  ones, sorted by URL

### Requirement: npm-installed tools are installed from a committed lockfile
openspec and renovate SHALL be installed from the committed
`scripts/lib/npm-tools/package-lock.json` with a lockfile-exact install
that rejects any drift between `package.json` and the lockfile, and that
does not run package install scripts. `task setup` SHALL reinstall when
the committed lockfile differs from the one last installed, not only when
a tool's own version differs.

#### Scenario: The lockfile changes without a version change
- **WHEN** `package-lock.json` changes a transitive dependency while
  openspec's and renovate's own versions stay the same, and `task setup`
  is run
- **THEN** the npm tools are reinstalled from the new lockfile

#### Scenario: versions.sh and the lockfile disagree
- **WHEN** an npm tool's version in `scripts/lib/versions.sh` differs
  from the one the lockfile was generated for
- **THEN** `task setup` fails instead of resolving a new version, and
  `task tools:npm-lock` regenerates the lockfile

### Requirement: Renovate refreshes content pins with version bumps
When Renovate bumps a pinned version, the same pull request SHALL also
carry the refreshed content pin: `scripts/lib/checksums.txt` regenerated
for a `scripts/lib/versions.sh` bump and `package-lock.json` regenerated
for an openspec or renovate bump, via post-upgrade tasks limited to
exactly those two generator scripts.

#### Scenario: Renovate bumps shellcheck
- **WHEN** Renovate opens a pull request changing `SHELLCHECK_VERSION`
- **THEN** that pull request also changes the shellcheck lines of
  `scripts/lib/checksums.txt`, and `task setup` succeeds on its branch
