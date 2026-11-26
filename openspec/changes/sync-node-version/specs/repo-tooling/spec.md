# Spec Delta

## ADDED Requirements

### Requirement: Node installs use NODE_VERSION
Every install of Node.js in this repo SHALL take its version from
`NODE_VERSION` in `scripts/lib/versions.sh`. An install SHALL NOT carry
a second copy of that version. This covers the local toolchain install,
frontend CI, and the UI image (`docker/Dockerfile.ui` and every build
that uses it). An image or workflow that does not install Node SHALL
stay that way. If one of those later gains a Node install, that install
SHALL use `NODE_VERSION` too.

#### Scenario: Frontend CI sets up Node
- **WHEN** the frontend CI workflow sets up Node
- **THEN** the version it passes is `NODE_VERSION` read from
  `scripts/lib/versions.sh` during the job, and the workflow file does
  not contain a Node version literal

#### Scenario: The UI image is built
- **WHEN** the UI image is built locally or in CI
- **THEN** the Node base image tag is `NODE_VERSION` supplied as a build
  argument, and the build fails when that argument is missing

#### Scenario: A Python agent image does not install Node
- **WHEN** `docker/Dockerfile.python-agent` is built
- **THEN** the image still has no Node install, and the build is not
  required to receive `NODE_VERSION`

#### Scenario: A new Node install names a different version
- **WHEN** a Dockerfile or workflow installs Node at a version other
  than `NODE_VERSION`
- **THEN** the standing Node version check fails and names that file

### Requirement: Node consumers that cannot read the variable match NODE_VERSION
A frontend `package.json` `engines.node` value, the committed UI base
image digest, and each doc that states which Node version to install
SHALL match `NODE_VERSION`. `engines.node` SHALL be `>=` followed by
`NODE_VERSION`. The committed digest SHALL be the digest of the
`node:<NODE_VERSION>-alpine` manifest list, and the UI Dockerfile SHALL
pin that digest.

#### Scenario: The engine floor matches the pin
- **WHEN** the Node version check runs and both frontend `package.json`
  files set `engines.node` to `>=` plus the current `NODE_VERSION`
- **THEN** that part of the check passes

#### Scenario: The engine floor is a different version
- **WHEN** either frontend `package.json` sets `engines.node` to a floor
  other than the current `NODE_VERSION`
- **THEN** the check fails and names that file

#### Scenario: The image digest is for a different Node version
- **WHEN** `NODE_VERSION` changes and the committed UI image digest is
  still the digest recorded for the previous version
- **THEN** the check fails, and a UI image build that used the stale
  digest is not treated as satisfying the new pin

#### Scenario: A doc states a different Node version
- **WHEN** `TUTORIAL.md`, either app README, or either frontend README
  states a Node version other than `NODE_VERSION`
- **THEN** the check fails and names that file

### Requirement: One standing check enforces the Node pin
`task versions:check` SHALL read `NODE_VERSION` and enforce the two
requirements above. It SHALL be one script, with one function for Node.
It SHALL run as part of `task check:all`.

#### Scenario: Node agrees everywhere it is installed
- **WHEN** `task versions:check` runs and every Node install reads
  `NODE_VERSION`, and every literal consumer matches it
- **THEN** the command exits zero

## MODIFIED Requirements

### Requirement: Renovate refreshes content pins with version bumps
When Renovate bumps a pinned version, the same pull request SHALL also
carry the refreshed content pin: `scripts/lib/checksums.txt` regenerated
for a `scripts/lib/versions.sh` bump, `package-lock.json` regenerated
for an openspec or renovate bump, and, when `NODE_VERSION` changes, the
UI base image digest plus the Node literals the version check compares
(`engines.node` and the docs that state the Node version). Those
refreshes SHALL run via post-upgrade tasks limited to the checksum
generator, the npm lockfile generator, and the Node consumer generator.

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
