# Design

## Context

See proposal.md for why. `scripts/setup.sh` and `scripts/lib/assets.sh`
already install every tool from `scripts/lib/versions.sh`. Node's other
installs were moved onto `NODE_VERSION` by `sync-node-version`. Two
copies remain, and one has drifted:

- `.github/workflows/helm-package-reusable.yaml` passes `version:
  "4.3.0"` to `azure/setup-helm`. `HELM_VERSION` is `v4.3.0`.
- `docker/Dockerfile.python-agent` is
  `astral/uv:0.11.16-python3.13-trixie-slim` plus a digest.
  `UV_VERSION` is `0.12.23`.

`scripts/lib/npm_tools.sh` already writes the openspec and renovate
versions from the pins. The committed lockfile and the `generatedBy`
stamps in the six `openspec-*` skills currently match. The
pinned-tool-versions rule quotes the live shfmt and task versions only
as examples of who prints a leading `v`.

`sync-node-version` is complete and not archived. Its delta says
`versions:check` has no function for any other pin and still exits zero
when another pin has drifted. This change replaces that limit. Archive
`sync-node-version` first. Before that archive, drop the "no other pin"
sentences from that delta so they are not applied onto the main spec
and then contradicted here. This change's Renovate requirement is the
superset: it keeps the Node refresh that delta added and adds the uv
digest.

## Goals / Non-Goals

**Goals:**

- One reader path per pin that can source `versions.sh`, and one
  checked literal per pin that cannot.
- The same failure mode as Node: a missing build-arg fails the build,
  and `task versions:check` fails when a literal disagrees.

**Non-Goals:**

- Pinning Python, Debian, dir-ctl, or dir-mcp in `versions.sh`.
- Treating the `astral-sh/setup-uv` action version, or a `# v4.3.0`
  comment on `docker/setup-buildx-action`, as a tool pin. Those name
  the GitHub Action, not uv or Helm.
- Rewriting changelog history or archived OpenSpec changes.
- Generating the `v` prefix examples. They stop quoting live versions.

## Decisions

### 1. uv follows the Node image pattern

`docker/Dockerfile.python-agent` gains `ARG UV_VERSION` with no default
and `FROM astral/uv:${UV_VERSION}-python3.13-trixie-slim@<digest>`.
The `ARG` is declared before the first `FROM`. Docker only lets a later
`FROM` read an arg declared in that global scope.
`scripts/lib/uv-image.txt` stores `<UV_VERSION> sha256:<64 hex>`, the
manifest-list digest of that tag. `scripts/tools/update_uv_image.bash`
and `task tools:sync-uv` rewrite the record and the `@sha256:` when the
recorded version differs, and exit without network when it already
matches. Callers pass the arg:

- `scripts/env.sh` exports `UV_VERSION` the same way it exports
  `NODE_VERSION`, and still exports nothing else.
- Every compose service that builds `docker/Dockerfile.python-agent`
  passes `UV_VERSION` with the same unset guard as `NODE_VERSION`.
- `.github/workflows/docker-build-reusable.yaml` sources
  `versions.sh` and passes `UV_VERSION` only when the dockerfile is
  `docker/Dockerfile.python-agent`.

Alternative considered: leave the Dockerfile on `0.11.16` and change
`UV_VERSION` to match it. Rejected. The pin is the source of truth, and
the local toolchain already installs `0.12.23`. The image is the copy
that drifted.

### 2. Helm CI sources the pin and strips one leading v

`HELM_VERSION` is `v4.3.0` because `helm version` prints the `v` and
`setup.sh` compares against that. The workflow today passes `4.3.0`
with no `v`. A step sources `versions.sh` and passes `${HELM_VERSION#v}`
to `azure/setup-helm`. The check fails when that `version:` input is a
numeric literal, and it does not treat the buildx action comment as a
Helm pin.

### 3. The other pins are guarded, not given new generators

actionlint, bats, shellcheck, shfmt, and task have no second install.
The check asserts `scripts/setup.sh` and `scripts/lib/assets.sh` still
expand each variable, and fails if a workflow or Dockerfile line
installs one of them with a numeric version.

The npm lockfile and the OpenSpec `generatedBy` stamps are literals
that cannot source the shell file. The check compares them to
`OPENSPEC_VERSION` and `RENOVATE_VERSION`. The existing
`task tools:npm-lock` remains the lockfile fix. `openspec update`
remains the stamp fix. Neither is copied into the uv generator.

The pinned-tool-versions sentence is reworded so a shfmt or task bump
does not edit it.

### 4. Renovate may still update the other images in the Python Dockerfile

The Node Dockerfile is disabled for the dockerfile manager because its
only `FROM` is the Node image. `docker/Dockerfile.python-agent` also
has dir-ctl and dir-mcp `FROM` lines, and those should keep updating.
Disable the dockerfile manager for the `astral/uv` image only. The uv
generator refreshes the digest when `UV_VERSION` changes. The version
check fails if the `FROM` line becomes a numeric tag.

## Risks / Trade-offs

- The `0.12.23` tag might not exist in the `python3.13-trixie-slim`
  form, or a build on it might fail. Mitigation: the implementation
  fetches the manifest and builds one Python agent image before the
  task is done. If the tag is absent, stop and report it. Do not invent
  a digest.
- A package rule might not be able to disable only `astral/uv`.
  Mitigation: the generator rewrites the `FROM` line back to the `ARG`
  form in the same post-upgrade run, and the check still fails a
  numeric tag.
- Archiving `sync-node-version` after this change can put the "ignore
  other pins" requirement back into the main spec. Mitigation: archive
  that change first, with those sentences already removed from its
  delta.

## Migration Plan

`source scripts/env.sh` before `docker compose` or `docker build` of a
Python agent image, the same step the UI image already requires. A
build without `UV_VERSION` fails instead of using `0.11.16`.

Rollback is reverting the Dockerfile `FROM` line, the compose args, and
the workflow step together. Leaving the `ARG` in place without the
callers passing it breaks every Python image build.
