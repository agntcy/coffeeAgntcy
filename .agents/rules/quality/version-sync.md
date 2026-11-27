---
name: version-sync
description: >-
  Every pin in scripts/lib/versions.sh is the only copy of that tool.
  Installs read it. Image digests and other literals that cannot read the
  variable are rewritten from it and checked by task versions:check. Apply
  when changing a pin, a Node or uv install, docker/Dockerfile.ui,
  docker/Dockerfile.python-agent, a frontend engines field, or a doc that
  states the Node version.
---

# Node version sync

## Rule

`NODE_VERSION` in
[`scripts/lib/versions.sh`](../../../scripts/lib/versions.sh) is the only
Node.js version this repo pins. Every install reads that variable:

- [`scripts/setup.sh`](../../../scripts/setup.sh) installs `.tools/node`
  from it.
- Frontend CI
  ([`.github/workflows/fe-ci.yaml`](../../../.github/workflows/fe-ci.yaml))
  sources the file and passes the value to `actions/setup-node`.
- [`docker/Dockerfile.ui`](../../../docker/Dockerfile.ui) takes
  `ARG NODE_VERSION` with no default. The corto and lungo UI services, and
  [`.github/workflows/docker-build-reusable.yaml`](../../../.github/workflows/docker-build-reusable.yaml),
  pass it. A build without it fails.

Consumers that cannot read a shell variable match the same pin.
[`task tools:sync-node`](../../../Taskfile.yaml) rewrites them from
`NODE_VERSION`:

- [`scripts/lib/node-image.txt`](../../../scripts/lib/node-image.txt) and
  the `@sha256:` in `docker/Dockerfile.ui` are the manifest-list digest of
  `node:<NODE_VERSION>-alpine`. Docker pulls by digest, so a tag change
  that leaves the old digest in place still runs the old Node.
- Both frontend `package.json` files, and the root `engines` object in
  each lockfile, set `engines.node` to `>=` plus `NODE_VERSION`.
- `TUTORIAL.md`, both app READMEs, and both frontend READMEs state that
  version and name `NODE_VERSION`.

`task versions:check`
([`scripts/checks/check_versions.bash`](../../../scripts/checks/check_versions.bash))
fails when any of those drift. It has one function per pin in
`versions.sh`, and it runs inside `task check:all`.

The same check covers the other pins. The map of every pin is [docs/tool-versions.md](../../../docs/tool-versions.md), and the Node procedure is [docs/node-version.md](../../../docs/node-version.md).

- `docker/Dockerfile.python-agent` takes `ARG UV_VERSION` with no default.
  `scripts/lib/uv-image.txt` and the `@sha256:` on that `FROM` line are
  the manifest-list digest of
  `astral/uv:<UV_VERSION>-python3.13-trixie-slim`. `task tools:sync-uv`
  rewrites them. `python3.13-trixie-slim` stays a literal.
- Helm CI
  ([`.github/workflows/helm-package-reusable.yaml`](../../../.github/workflows/helm-package-reusable.yaml))
  sources `HELM_VERSION` and passes it without the leading `v`.
- Python tests
  ([`.github/workflows/test-reusable.yaml`](../../../.github/workflows/test-reusable.yaml))
  source `scripts/lib/versions.sh` and export `NODE_VERSION` and
  `UV_VERSION` before pytest. The integration tests run `docker compose`,
  which reads those variables.
- The npm tools lockfile records `OPENSPEC_VERSION` and
  `RENOVATE_VERSION`. Each OpenSpec skill `generatedBy` stamp equals
  `OPENSPEC_VERSION`.
- actionlint, bats, shellcheck, shfmt, and task are installed only by
  `scripts/setup.sh` and `scripts/lib/assets.sh`, which read the
  variables. A numeric install of one of them in a workflow or
  Dockerfile fails the check.

Renovate's dockerfile manager is disabled for the `astral/uv` package in
`docker/Dockerfile.python-agent` only. The dir-ctl and dir-mcp `FROM`
lines in that file stay managed. A `UV_VERSION` bump still refreshes the
digest: the toolchain post-upgrade tasks run
`scripts/tools/update_uv_image.bash`.

Renovate's dockerfile manager substitutes an empty `ARG NODE_VERSION` and
would rewrite the `FROM` line, so `docker/Dockerfile.ui` is disabled for
that manager in
[`renovate.json`](../../../renovate.json). A `NODE_VERSION` bump still
refreshes the digest: the toolchain post-upgrade tasks run
`scripts/tools/update_node_version.bash`.

`docker/Dockerfile.python-agent` does not install Node. The check fails if
a Dockerfile or workflow starts installing a different version. It does
not add a Node install there.

## Why

A second copy of the Node version drifts. Renovate was bumping the
workflow, the image tag, and `NODE_VERSION` in different pull requests,
and nothing failed when they disagreed. Reading the variable removes the
copies that can read it. The check keeps the copies that cannot.

## How to apply

- Change `NODE_VERSION` only in `scripts/lib/versions.sh`. Then run
  `task tools:checksums` (the Node tarball hashes) and
  `task tools:sync-node`, and review the digest against
  `docker buildx imagetools inspect node:<version>-alpine`. Then run
  `task versions:check`.
- Do not put a Node version literal in a workflow `node-version:`, a
  `FROM node:` tag, or a compose `NODE_VERSION` value.
- After bumping `UV_VERSION`, run `task tools:sync-uv`, and review the
  digest against
  `docker buildx imagetools inspect astral/uv:<version>-python3.13-trixie-slim`.
  Then run `task versions:check`.
- `source scripts/env.sh` before a local UI or Python agent image build.
  It exports `NODE_VERSION` and `UV_VERSION`, and no other pin.
- See the `checking-version-sync` skill for the check workflow.
