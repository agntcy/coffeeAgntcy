---
name: version-sync
description: >-
  NODE_VERSION in scripts/lib/versions.sh is the only Node.js pin. Installs
  read it. The UI image digest, frontend engines.node floors, and the docs
  that state the Node version are rewritten from it by task tools:sync-node
  and checked by task versions:check. Apply when changing a Node install,
  NODE_VERSION, docker/Dockerfile.ui, a frontend engines field, or those docs.
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
fails when any of those drift. The script has one function, `check_node`.
Other pins in `versions.sh` are not checked. The check runs inside
`task check:all`.

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
- `source scripts/env.sh` before a local UI image build. It exports
  `NODE_VERSION` and no other pin.
- See the `checking-version-sync` skill for the check workflow.
