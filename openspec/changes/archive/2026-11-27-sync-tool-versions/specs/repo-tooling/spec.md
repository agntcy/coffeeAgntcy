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

#### Scenario: Another action in that workflow has a version input
- **WHEN** a step other than `azure/setup-helm` in the Helm package
  workflow sets a numeric `version:` input
- **THEN** the Helm part of the version check does not fail on it

### Requirement: CI installs the uv CLI at UV_VERSION
Every workflow step that uses `astral-sh/setup-uv` SHALL pass
`UV_VERSION` from `scripts/lib/versions.sh` as its `version:` input. The
workflow SHALL export `UV_VERSION` from that file before the step runs.
A step with no `version:` input or a literal one SHALL fail the check.

#### Scenario: A workflow sets up uv
- **WHEN** a workflow uses `astral-sh/setup-uv`
- **THEN** its `version:` input reads `UV_VERSION` from the job env,
  which the workflow exported from `scripts/lib/versions.sh`

#### Scenario: A workflow sets up uv without a version
- **WHEN** a `setup-uv` step has no `version:` input or a numeric one
- **THEN** the standing version check fails

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
of them anywhere else, at any version or none, SHALL fail the version
check. A workflow that uses an action which installs one of them SHALL
fail the check, whatever the action's tag.

#### Scenario: A workflow installs one of those tools elsewhere
- **WHEN** a workflow or Dockerfile installs actionlint, bats,
  shellcheck, shfmt, or task with a package manager, an installer
  script, or a release download, with or without a version
- **THEN** the version check fails and names that file

#### Scenario: A comment mentions an install
- **WHEN** a workflow or Dockerfile comment line mentions installing one
  of those tools and no other line installs it
- **THEN** that part of the check passes

#### Scenario: A workflow uses an action for one of those tools
- **WHEN** a workflow has a `uses:` line for an action that installs
  actionlint, bats, shellcheck, shfmt, or task
- **THEN** the version check fails and names that file and the tool,
  whatever the action's version tag

### Requirement: The version check reads active lines and whole steps
`task versions:check` SHALL ignore full-line comments, SHALL read an
action's version input from the whole step that uses it, and SHALL check
each compose build block on its own. A comment SHALL NOT satisfy or
trigger a check. An `actions/setup-node` or `azure/setup-helm` step
whose version input is missing, is a literal, or is any expression other
than `${{ env.<PIN> }}` or `${{ steps.<id>.outputs.<name> }}` SHALL fail,
in any workflow and in any YAML form. A compose build block that names
`docker/Dockerfile.ui` or `docker/Dockerfile.python-agent` SHALL pass its
build arg as `${VAR:?...}`, and a default or literal SHALL fail. An
OpenSpec skill with no `generatedBy` stamp SHALL fail.

#### Scenario: A comment mentions the export
- **WHEN** the Python test workflow contains the pin export only inside
  comment lines
- **THEN** the version check fails and names that file

#### Scenario: A setup-helm step is written as an inline mapping
- **WHEN** a workflow has a step written as one flow mapping that uses
  `azure/setup-helm` and sets `version` to `4.3.0`
- **THEN** the version check fails and names that file

#### Scenario: One compose service leaves out the build arg
- **WHEN** one service in a compose file builds
  `docker/Dockerfile.python-agent` and another service in the same file
  passes `UV_VERSION`
- **THEN** the version check fails and names the service's `build:` line

### Requirement: Digest generators refuse single-platform manifests
`scripts/tools/update_node_version.bash` and
`scripts/tools/update_uv_image.bash` SHALL record a digest only when the
final registry response has a manifest-list or OCI index content type,
and SHALL otherwise fail without changing any file.

#### Scenario: The registry returns a single-platform manifest
- **WHEN** the manifest response has a single-platform content type
- **THEN** the script exits non-zero and leaves the digest record and
  Dockerfile unchanged

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
for an openspec or renovate bump, the OpenSpec skill `generatedBy`
stamps regenerated for an openspec bump, the UI image digest and Node
literals when `NODE_VERSION` changes, and the Python agent uv image
digest when `UV_VERSION` changes. Those refreshes SHALL run via
post-upgrade tasks limited to the checksum generator, the npm lockfile
generator, the OpenSpec skill generator, the Node consumer generator,
and the uv image generator.

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

#### Scenario: Renovate bumps openspec
- **WHEN** Renovate opens a pull request changing `OPENSPEC_VERSION`
- **THEN** that pull request also updates the npm lockfile and every
  OpenSpec skill `generatedBy` stamp, and `task versions:check` passes
  on its branch

#### Scenario: Renovate bumps uv
- **WHEN** Renovate opens a pull request changing `UV_VERSION`
- **THEN** that pull request also updates the uv tarball checksums and
  the Python agent image digest, and `task versions:check` passes on
  its branch
