# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
