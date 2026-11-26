# Design

## Context

See proposal.md for why. The constraints that shape the approach:

- `scripts/lib/versions.sh` is already the pin `scripts/setup.sh` installs,
  and Renovate's custom manager bumps it. `scripts/lib/assets.sh` and
  `scripts/lib/checksums.txt` are derived from it.
- Frontend CI (`.github/workflows/fe-ci.yaml`) and `docker/Dockerfile.ui`
  repeat `26.13.1` as literals. Renovate bumps them in the Github Actions
  group and the Docker group, separate from the toolchain group.
- Both frontend `package.json` files set `engines.node` to `>=26.13.1`,
  and each `.npmrc` sets `engine-strict=true`. npm cannot read a shell
  variable, so that floor stays a literal.
- `docker/Dockerfile.python-agent` is the image for every Python service
  (corto exchange and farm, lungo supervisors, farms, the workflow API).
  It installs uv and Python. It does not install Node, and no agent code
  runs Node. "The same Node everywhere" means every current Node install,
  not a new install inside that image.
- `openspec/specs/repo-operation-governance/spec.md` already says no tool
  version is hardcoded outside `versions.sh`. Nothing enforces that. This
  change enforces it for Node only. The uv drift (`Dockerfile.python-agent`
  is `0.11.16`, `UV_VERSION` is `0.12.23`) stays out of scope.
- The governance spec also says a version-bump workflow does not get its
  own CI check. That exception is about the one-shot bump. A standing
  drift check is a different operation and belongs in `task check:all`.
- `task pins:check` already requires the UI base image to carry
  `@sha256:`. Docker pulls by digest, so a tag change that leaves the old
  digest in place still runs the old Node.
- New checks follow the five-layer pipeline. Bash scripts need bats tests.
  `scripts/checks/tests/check_all.bats` and the "all twelve" wording in
  `.agents/rules/always-apply/pre-finalize-checks.md` assume today's check
  count.

## Goals / Non-Goals

**Goals:**

- Places that can execute shell read `NODE_VERSION` at install time.
- Places that cannot (npm `engines`, markdown, the image digest) are
  rewritten from that variable and rejected by one check when they
  disagree.
- One script, one function for Node. A later pin is another function in
  the same script, not another task.

**Non-Goals:**

- Installing Node into `docker/Dockerfile.python-agent` or any agent
  process.
- Checking or aligning uv, Helm, Python, npm, or any other
  `versions.sh` pin.
- Changing `engines.node` from a floor (`>=`) to an exact pin.
- Folding Node into the shared application package catalog. That catalog
  is for npm and Python package pins, and its design leaves `engines`
  alone.

## Decisions

### 1. Reads where a process can, copies only where it cannot

| Consumer | How it gets the version |
|---|---|
| `scripts/setup.sh` | Already expands `$NODE_VERSION`. Unchanged. |
| `.github/workflows/fe-ci.yaml` | A step sources `scripts/lib/versions.sh` and passes the step output to `actions/setup-node`. No `node-version` literal. |
| `docker/Dockerfile.ui` | `ARG NODE_VERSION` with no default. `FROM node:${NODE_VERSION}-alpine@sha256:<digest>`. |
| Compose UI services and the documented `docker build` lines | Pass `NODE_VERSION` through. Missing value fails the build. |
| CI image builds of `docker/Dockerfile.ui` | `docker-build-reusable.yaml` sources `versions.sh` and appends `NODE_VERSION` to the build-args only when the dockerfile is `docker/Dockerfile.ui`. |
| Frontend `package.json` / root `engines` in the matching lockfiles | Literal `>=${NODE_VERSION}`, rewritten by the generator. |
| `TUTORIAL.md`, both app READMEs, both frontend READMEs | The Node sentence states `NODE_VERSION`'s value and names the variable. Rewritten by the generator. |

`scripts/env.sh` exports `NODE_VERSION` and no other pin, so
`source scripts/env.sh` is enough for Compose. Compose project `.env`
files are not given a `NODE_VERSION` line. The shell value wins, and an
unset value hits the `:?` guard.

Alternatives considered:

- Leave the literals and only compare them in a check. Rejected for the
  installs. A check that passes today and fails after a forgotten edit
  still leaves three Renovate groups moving the same number. Reading the
  variable removes the CI and Dockerfile copies from those groups.
- Generate the workflow and the Dockerfile tag from `versions.sh` at
  image-build time only, and keep a committed literal as a fallback.
  Rejected. The fallback is a second pin.

### 2. The digest is a committed record, refreshed with the pin

`scripts/lib/node-image.txt` holds one line: the current `NODE_VERSION`
and the manifest-list digest of `node:<NODE_VERSION>-alpine`. The
Dockerfile's `@sha256:` equals that digest. `task pins:check` keeps
requiring the digest. The version check requires the record's version
field to equal `NODE_VERSION` and the Dockerfile digest to equal the
record.

The generator requests the manifest-list media type from the Docker Hub
registry. A single-arch manifest digest would not match what
`FROM node:<version>-alpine` resolves to on a multi-platform pull.
No new CLI is added. The first fetch is trust-on-first-use, reviewed in
the pull request, same as `scripts/lib/checksums.txt`.

The generator is `scripts/tools/update_node_version.bash`, wrapped by
`task tools:sync-node` and nothing else. It rewrites
the digest record, the Dockerfile digest, both `engines.node` floors
(package.json and the root engines object in each package-lock.json),
and the Node sentence in the five docs. It is idempotent when
`NODE_VERSION` already matches. It does not run `npm install`. The root
`engines` field is metadata npm copies into the lockfile. Transitive
`engines` inside dependencies are left alone.

Renovate's toolchain `postUpgradeTasks` gains this script next to the
checksum and npm-lock generators. `.github/workflows/renovate.yaml`
allows that command and no others beyond the ones it already allows.
On a shellcheck-only bump the script exits without network, because the
record already matches `NODE_VERSION`.

Alternatives considered:

- Let the Dockerfile manager keep owning the digest, and group it with
  the `versions.sh` bump. Rejected. An `ARG` tag is not a version the
  dockerfile manager extracts, and a grouped pair can still merge one
  side without the other.
- Verify the digest against the registry inside `task versions:check`.
  Rejected. `task check:all` stays offline.

### 3. One script, one function, Node only

`scripts/checks/check_versions.bash` sources `versions.sh` and calls
`check_node`. The header says other pins are not checked, and that a new
pin is a new function in this file. The task is `versions:check`. It is
added to `scripts/checks/check_all.bash`.

`check_node` fails closed:

- Every `node-version:` under `.github/workflows/` is the step output
  from a step that sources `scripts/lib/versions.sh`. A numeric literal
  fails.
- Every `node:` image reference uses `${NODE_VERSION}` (or the compose
  build-arg that passes it) and the digest from `node-image.txt`. A
  numeric tag fails. `docker/Dockerfile.python-agent` has no such
  reference and is not required to grow one.
- Every `docker-compose*.yaml` and CI build of `Dockerfile.ui` passes
  `NODE_VERSION` and does not assign it a literal.
- `scripts/setup.sh`'s Node install still expands `NODE_VERSION`.
- Each frontend `package.json` `engines.node` is `>=` plus
  `NODE_VERSION`, and the lockfile root engines field says the same.
- The five docs contain that same version in the Node install sentence.
  The check looks for that sentence. A missing sentence fails, so a
  reword that drops the version does not pass silently.
- It does not scan the repo for the word "node". Workflow graph ids,
  SLIM node tags, and `@types/node` are not Node.js installs.

Bats tests follow `check_pinned_references.bats`: copy the script into a
fixture repo whose `SCRIPT_DIR` layout matches, and cover one passing
tree plus one failure per bullet above.

### 4. Pipeline layers

Script `scripts/checks/check_versions.bash`, task `versions:check`,
skill `.agents/skills/quality-checks/checking-version-sync/SKILL.md`,
CI via `check_all.bash` only (no new workflow), rule
`.agents/rules/quality/version-sync.md`. Index both in `AGENTS.md`.
Add a `pre-finalize-checks.md` row and change "all twelve" to "all
thirteen", including the same count in `check_all.bats` and
`.github/workflows/README.md`.

`pinned-tool-versions` and `manage-repo-tooling` gain a step: after
changing `NODE_VERSION`, run the generator, then `task versions:check`.
They do not grow a second source of truth.

## Risks / Trade-offs

- [A manifest-list digest is fetched with the wrong Accept header and
  does not match the tag] → The implementation task compares one fetch
  against `docker buildx imagetools inspect node:26.13.1-alpine` before
  committing the record. The check then only compares committed files.
- [Compose is run in a shell that has not sourced `scripts/env.sh`] →
  The build fails with the `:?` message. The UI docker READMEs say to
  source it first. This is the breaking change in the proposal.
- [Renovate's dockerfile manager still rewrites `FROM node:${NODE_VERSION}...`
  into a numeric tag] → Confirm against the current Renovate docs during
  implementation. If it does, disable that manager for `docker/Dockerfile.ui`
  with a `matchFileNames` rule, and say so in the rule.
- [`package-lock.json` root `engines` is rewritten by a later `npm install`
  to a different floor] → The check covers the lockfile root as well as
  `package.json`, so the drift fails `task versions:check`.
- [The governance spec still says no tool version is hardcoded, and uv
  remains hardcoded] → Stated as a non-goal. The script header names it
  so the next function has an obvious home.

## Migration Plan

1. Add the digest record for the Node version already in `versions.sh`,
   without changing `NODE_VERSION`.
2. Switch fe-ci, the Dockerfile, compose, and the reusable workflow to
   read the variable. The digest string stays the one already pinned, so
   the image bytes do not change.
3. Point the five docs and both engine floors at that same value. They
   already say `26.13.1`, so this is a wash if the pin has not moved.
4. Land the check, the bats tests, and the pipeline layers. The check
   passes on the migrated tree.
5. Add the generator to Renovate's allowed commands and post-upgrade
   tasks.

Rollback is reverting the commit. No data migration. Images already
pushed keep the digest they were built with.

Documentation to update in the same change, beyond the new rule and
skill: `AGENTS.md`, `pre-finalize-checks.md`, `pinned-tool-versions.md`,
`manage-repo-tooling` and `setup-repo-tooling` (the env export),
`CONTRIBUTING.md` if it lists the check set, `.github/workflows/README.md`,
`TUTORIAL.md`, both app READMEs, both frontend READMEs, and
`docker/README.corto.md` and `docker/README.lungo.md`.

## Open Questions

None. Scope is Node installs that exist today, plus a check that fails
if a new install does not use `NODE_VERSION`.
