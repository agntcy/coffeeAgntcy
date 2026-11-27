# repo-tooling Specification

## Purpose
Defines this repo's own development tooling: a repo-local pinned
toolchain bootstrap, the five-layer script/task/skill/CI/rule pattern
every repo operation follows, the standing checks built on that pattern,
and the CI workflow that runs them all together.

## Requirements

### Requirement: A repo-local toolchain installs without touching the global system
`task setup` (equivalently `./scripts/setup.sh`) SHALL install `task`,
`actionlint`, `shellcheck`, `shfmt`, `bats`, `uv`, `helm`, `node`,
`openspec`, and `renovate` into this repo's own `.tools/` directory, and
SHALL NOT modify the invoking user's global `PATH`, shell profile, or home
directory. `source scripts/env.sh` SHALL put `.tools/bin`,
`.tools/node/bin`, and `.tools/bats/bin` on `PATH` for the invoking shell
session only.

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
