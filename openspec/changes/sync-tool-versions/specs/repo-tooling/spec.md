# Spec Delta

## ADDED Requirements

### Requirement: The Python agent image uses UV_VERSION
`docker/Dockerfile.python-agent` SHALL take its uv base image tag from
`UV_VERSION` in `scripts/lib/versions.sh`, supplied as a build argument
with no default. A build SHALL fail when that argument is missing. The
image SHALL pin the digest of
`astral/uv:<UV_VERSION>-python3.13-trixie-slim`. The `python3.13` and
`trixie-slim` parts of the tag SHALL stay literals.

#### Scenario: The Python agent image is built
- **WHEN** a Python agent image is built locally or in CI
- **THEN** the uv tag is `UV_VERSION` supplied as a build argument, and
  the build fails when that argument is missing

#### Scenario: The uv digest is for a different version
- **WHEN** `UV_VERSION` changes and the committed uv image digest is
  still the digest recorded for the previous version
- **THEN** the standing version check fails, and a build that used the
  stale digest is not treated as satisfying the new pin

### Requirement: Helm CI uses HELM_VERSION
The workflow that packages Helm charts SHALL install Helm from
`HELM_VERSION` in `scripts/lib/versions.sh`. That workflow file SHALL
NOT contain a Helm version literal.

#### Scenario: Helm CI installs Helm
- **WHEN** the Helm package workflow sets up Helm
- **THEN** the version it passes is read from `HELM_VERSION` during the
  job, and the workflow file does not contain a Helm version literal

### Requirement: npm tool pins and OpenSpec skill stamps match versions.sh
The committed npm tools lockfile SHALL record openspec at
`OPENSPEC_VERSION` and renovate at `RENOVATE_VERSION`. Each generated
OpenSpec skill stamp SHALL equal `OPENSPEC_VERSION`.

#### Scenario: The lockfile matches the npm pins
- **WHEN** the version check runs and the lockfile's openspec and
  renovate versions equal `OPENSPEC_VERSION` and `RENOVATE_VERSION`
- **THEN** that part of the check passes

#### Scenario: A skill stamp disagrees
- **WHEN** a generated OpenSpec skill stamp is not `OPENSPEC_VERSION`
- **THEN** the version check fails and names that file

### Requirement: Tools with no second install stay single-sourced
actionlint, bats, shellcheck, shfmt, and task SHALL be installed only
by the local toolchain, which SHALL read the matching variable in
`scripts/lib/versions.sh`. A workflow or Dockerfile that installs one
of them at a numeric version SHALL fail the version check.

#### Scenario: A workflow hardcodes one of those tools
- **WHEN** a workflow or Dockerfile installs actionlint, bats,
  shellcheck, shfmt, or task at a numeric version
- **THEN** the version check fails and names that file

### Requirement: versions:check covers every pin
`task versions:check` SHALL enforce the requirements in this change and
the Node pin requirements. It SHALL run as part of `task check:all`.

#### Scenario: Every pin agrees
- **WHEN** `task versions:check` runs and every install reads its pin,
  and every literal consumer matches that pin
- **THEN** the command exits zero

## MODIFIED Requirements

### Requirement: Renovate refreshes content pins with version bumps
When Renovate bumps a pinned version, the same pull request SHALL also
carry the refreshed content pin: `scripts/lib/checksums.txt` regenerated
for a `scripts/lib/versions.sh` bump, `package-lock.json` regenerated
for an openspec or renovate bump, the UI image digest and Node literals
when `NODE_VERSION` changes, and the Python agent uv image digest when
`UV_VERSION` changes. Those refreshes SHALL run via post-upgrade tasks
limited to the checksum generator, the npm lockfile generator, the Node
consumer generator, and the uv image generator.

#### Scenario: Renovate bumps shellcheck
- **WHEN** Renovate opens a pull request changing `SHELLCHECK_VERSION`
- **THEN** that pull request also changes the shellcheck lines of
  `scripts/lib/checksums.txt`, and `task setup` succeeds on its branch

#### Scenario: Renovate bumps Node
- **WHEN** Renovate opens a pull request changing `NODE_VERSION`
- **THEN** that pull request also updates the Node tarball checksums,
  the UI image digest, the frontend `engines.node` floors, and the docs
  that state the Node version, and `task versions:check` passes on its
  branch

#### Scenario: Renovate bumps uv
- **WHEN** Renovate opens a pull request changing `UV_VERSION`
- **THEN** that pull request also updates the uv tarball checksums and
  the Python agent image digest, and `task versions:check` passes on
  its branch
