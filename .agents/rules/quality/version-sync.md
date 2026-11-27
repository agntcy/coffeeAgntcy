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

# Version sync

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
  sources `HELM_VERSION` and passes it without the leading `v`. Only the
  `azure/setup-helm` step's `version:` input is checked, so another
  action's `version:` input in that file is not a Helm pin.
- Every `astral-sh/setup-uv` step in `.github/workflows/` passes
  `version: ${{ env.UV_VERSION }}` (or
  `${{ steps.<id>.outputs.UV_VERSION }}`), and its workflow exports
  `UV_VERSION` from `scripts/lib/versions.sh` first. A step with no
  `version:` input or a literal one fails the check, because the action
  would install its own choice of uv.
- Python tests
  ([`.github/workflows/test-reusable.yaml`](../../../.github/workflows/test-reusable.yaml))
  source `scripts/lib/versions.sh` and export `NODE_VERSION` and
  `UV_VERSION` before pytest. The integration tests run `docker compose`,
  which reads those variables.
- The npm tools lockfile records `OPENSPEC_VERSION` and
  `RENOVATE_VERSION`. Each OpenSpec skill `generatedBy` stamp equals
  `OPENSPEC_VERSION`. After an openspec bump, `task tools:sync-openspec`
  regenerates the stamps, and Renovate runs the same script.
- actionlint, bats, shellcheck, shfmt, and task are installed only by
  `scripts/setup.sh` and `scripts/lib/assets.sh`, which read the
  variables. Any other install of one of them in a workflow or
  Dockerfile fails the check, at any version: a package manager line
  (`apt-get`, `apk`, `brew`, `pip`, `npm`, `go install`, `snap`, `asdf`,
  ..., with flags before the verb allowed) that names it, the
  taskfile.dev install script, or a release download. So does a `uses:`
  of an action that installs one of them (for example
  `ludeeus/action-shellcheck`), whatever its tag, because it brings a
  second copy, and a pre-commit `repo:` that ships one. So does a tool
  name directly followed by a version (`shellcheck-v0.10.0`,
  `koalaman/shellcheck:v0.10.0`, `shellcheck 0.10.0`), and a literal
  assigned to a tool pin (`SHELLCHECK_VERSION: 0.10.0`). A tool name and
  an unrelated version that only share a line do not fail.
  Lines ending in `\` are joined first, so a package name on a
  continuation line is seen. Full-line and trailing `# ...` comments
  are skipped.
- That install check scans workflows, composite actions, Dockerfiles,
  `Taskfile*.y(a)ml`, compose files, `.pre-commit-config.yaml`, and
  shell scripts under `scripts/`. `scripts/setup.sh`,
  `scripts/lib/assets.sh`, `scripts/lib/versions.sh`, and
  `scripts/checks/` are exempt. It matches known shapes, not every way
  to install a tool: an unversioned tool image (`koalaman/shellcheck:stable`),
  a download from a mirror with no version, and a Node, uv, or Helm
  install that is not an action, an image, an `ARG`, or a version
  manager are not caught. Review those by hand.
- [`scripts/lib/checksums.txt`](../../../scripts/lib/checksums.txt) holds
  one SHA-256 for every archive URL that
  [`scripts/lib/assets.sh`](../../../scripts/lib/assets.sh) builds from
  the pins. The check lists those URLs from `assets.sh` and fails on a
  URL with no 64-hex checksum, and on a line no pin produces. After any
  bump of a downloaded tool, run `task tools:checksums`.
- The check compares versions. It does not notice a registry tag that
  moves under the same version, so a digest file stays as written until
  its version changes.

How the check reads a file, so a wrong shape fails and a harmless one
does not:

- Full-line comments are dropped before any match. A comment can neither
  satisfy a check (a `# . scripts/lib/versions.sh` line is not a source
  step) nor trip one.
- An action's version input is read per step. `actions/setup-node`
  needs `node-version:` and `azure/setup-helm` needs `version:`, each as
  `${{ env.<PIN> }}` or `${{ steps.<id>.outputs.<name> }}`. A missing
  input, a literal (including `v26.13.1`), another expression such as a
  matrix value, or `node-version-file:` fails. An inline flow mapping, a
  `with:` block before `uses:`, a quoted action, and a different case of
  the action name count. Every workflow is scanned, and so is any
  `HELM_VERSION` or `NODE_VERSION` literal assignment. A version manager
  install (`nvm install 20.1.0`) at a literal fails.
- Every compose `build:` block that names `docker/Dockerfile.ui` or
  `docker/Dockerfile.python-agent` passes its build arg as
  `${VAR:?...}`, so a service that leaves it out is named. A default
  (`:-`, `:=`) or a literal fails. The message is
  `run: source "$(git rev-parse --show-toplevel)/scripts/env.sh"`, which
  works from any directory. Docs that run `docker compose` or the
  integration tests tell the reader to run that line first.
- Any `FROM node:` or `image: node:` line (with `--platform` flags, a
  `docker.io/library/` prefix, or quotes) must use `${NODE_VERSION}`.
  Only `docker/Dockerfile.ui` must carry the digest in
  `scripts/lib/node-image.txt`, because another Node variant has its own.
- The root `engines.node` floor is the first one in a lockfile, before
  any `node_modules/` entry. A root entry with no `>=` floor is an error,
  never a dependency's floor.
- Every OpenSpec skill has a `generatedBy` stamp, quoted or not.
- The two digest generators accept only a manifest list or an OCI index,
  read from the last response, and refuse a single-platform manifest.
- A change to `scripts/lib/versions.sh` alone runs the Helm and image
  build workflows on a pull request, because both list it in their path
  filters.

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
