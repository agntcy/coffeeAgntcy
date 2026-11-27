# Spec Delta

## MODIFIED Requirements

### Requirement: A repo-local toolchain installs without touching the global system
`task setup` (equivalently `./scripts/setup.sh`) SHALL install `task`,
`actionlint`, `shellcheck`, `shfmt`, `bats`, `uv`, `helm`, `node`,
`openspec`, `renovate`, and `dir-mcp` into this repo's own `.tools/`
directory, and SHALL NOT modify the invoking user's global `PATH`, shell
profile, or home directory. `source scripts/env.sh` SHALL put `.tools/bin`,
`.tools/node/bin`, and `.tools/bats/bin` on `PATH` for the invoking shell
session only, so that `dir-mcp` is found by `shutil.which("dir-mcp")` and by
the shell afterwards.

#### Scenario: Fresh clone with no toolchain installed
- **WHEN** `task setup` is run in a clone with no `.tools/` directory
- **THEN** every tool listed above is installed under `.tools/`, and no
  file outside this repo's working tree is modified

#### Scenario: dir-mcp is available after setup
- **WHEN** `task setup` has run and `source scripts/env.sh` was sourced
- **THEN** `command -v dir-mcp` prints `.tools/bin/dir-mcp` and that file is
  the release asset for the running OS and architecture, whose SHA-256 matches
  the pin in `scripts/lib/checksums.txt`

### Requirement: Every pinned tool's version is checked for drift, not just presence
`scripts/lib/versions.sh` SHALL be the single place any tool's version is
pinned, including the npm-installed tools; any `package.json` used to
install them SHALL be generated from those pins, never separately
committed. `task setup` SHALL compare each tool's *installed* version against its pin and
reinstall on any mismatch - a tool already present at the wrong version
SHALL NOT be treated as satisfying the pin merely because a binary exists
at its expected path. For a tool whose binary cannot report its own version
(`dir-mcp`), `task setup` SHALL compare the version recorded when it was
installed, and SHALL reinstall it when that record is missing or differs from
the pin.

#### Scenario: A pin is bumped after the tool is already installed
- **WHEN** a tool's pinned version in `scripts/lib/versions.sh` is
  changed and `task setup` is run again
- **THEN** that tool is reinstalled at the newly pinned version, even
  though a binary from the old version was already present

#### Scenario: dir-mcp is already installed at the pinned version
- **WHEN** `task setup` is run again and `.tools/bin/dir-mcp` was installed at
  the version now pinned
- **THEN** `dir-mcp` is reported as already installed and nothing is fetched

#### Scenario: dir-mcp has no install record
- **WHEN** `.tools/bin/dir-mcp` exists but its install record is missing or
  names another version
- **THEN** `task setup` reinstalls `dir-mcp` at the pinned version

### Requirement: Renovate refreshes content pins with version bumps
When Renovate bumps a pinned version, the same pull request SHALL also
carry the refreshed content pin: `scripts/lib/sigstore/requirements.txt`
regenerated for a `SIGSTORE_VERSION` bump, `scripts/lib/checksums.txt`
regenerated for a `scripts/lib/versions.sh` bump, and `package-lock.json`
regenerated for an openspec or renovate bump, via post-upgrade tasks limited
to exactly those three generator scripts, run in that order (the sigstore
lock first, because the checksum generator installs the verifier from it).
A Renovate bump of `DIR_MCP_VERSION` SHALL only ever propose a release of the
`<major>.<minor>.<patch>-mcp.<build>` line, never a plain `<major>.<minor>.<patch>`
release, so the local binary stays on the line the compose files' image uses.

#### Scenario: Renovate bumps shellcheck
- **WHEN** Renovate opens a pull request changing `SHELLCHECK_VERSION`
- **THEN** that pull request also changes the shellcheck lines of
  `scripts/lib/checksums.txt`, and `task setup` succeeds on its branch

#### Scenario: Renovate bumps SIGSTORE_VERSION
- **WHEN** Renovate opens a pull request changing `SIGSTORE_VERSION`
- **THEN** that pull request also changes `scripts/lib/sigstore/requirements.txt`,
  and `task tools:checksums` succeeds on its branch

#### Scenario: A plain release of dir-mcp is published
- **WHEN** `agntcy/dir-mcp` publishes `v1.3.9` (no `-mcp.<build>` suffix) next
  to the `-mcp.<build>` line
- **THEN** Renovate does not propose it for `DIR_MCP_VERSION`

## ADDED Requirements

### Requirement: Checksum pins for dir-mcp come only from signature-verified assets
`task tools:checksums` SHALL verify each `dir-mcp` release asset against its
published sigstore bundle before recording the asset's SHA-256 in
`scripts/lib/checksums.txt`. The expected signer SHALL be the `dir-mcp`
repository's release workflow at the tag matching the pinned version, issued by
GitHub Actions. If verification fails for any platform, the task SHALL exit
non-zero and SHALL NOT write any checksum line for `dir-mcp`. `task setup`
SHALL keep verifying only the pinned SHA-256 and SHALL NOT need network access
beyond the download itself.

The verifier itself SHALL be installed only from a committed requirements file
that pins `sigstore` and every transitive package by SHA-256, with hash
checking enforced, and `task tools:checksums` SHALL refuse to run when that
file's `sigstore` version differs from the pin in `scripts/lib/versions.sh`.

#### Scenario: Genuine release asset
- **WHEN** `task tools:checksums` runs and every `dir-mcp` asset matches its
  bundle and expected signer
- **THEN** the four `dir-mcp` checksum lines are written

#### Scenario: Asset altered after signing
- **WHEN** an asset's bytes do not match its bundle's digest
- **THEN** the task fails naming the asset and writes no `dir-mcp` line

#### Scenario: Bundle signed by another identity
- **WHEN** a bundle verifies but its signer is not the expected release
  workflow at the pinned tag
- **THEN** the task fails and writes no `dir-mcp` line

#### Scenario: A verifier package does not match its pinned hash
- **WHEN** any package in the verifier's requirements file does not match its
  pinned SHA-256 at install time
- **THEN** the task fails before verifying anything and writes no `dir-mcp`
  line

#### Scenario: The verifier pin and its requirements file disagree
- **WHEN** `SIGSTORE_VERSION` is bumped without regenerating the requirements
  file
- **THEN** `task tools:checksums` fails naming `task tools:sigstore-lock`
