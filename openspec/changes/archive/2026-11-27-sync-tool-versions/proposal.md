# Proposal

## Why

`scripts/lib/versions.sh` pins every local tool, and `scripts/setup.sh`
installs from those variables. Node is the only pin whose other installs
are forced to read it. Helm CI still passes a literal, and
`docker/Dockerfile.python-agent` still names uv `0.11.16` while
`UV_VERSION` is `0.12.23`. Nothing fails when those copies disagree.

## What Changes

- Make every install of a `versions.sh` tool read that pin. The copies
  that do not today are Helm in
  `.github/workflows/helm-package-reusable.yaml` and uv in
  `docker/Dockerfile.python-agent`.
- **BREAKING** for local Python agent image builds: compose and the
  documented `docker build` lines require `UV_VERSION` (`source
  scripts/env.sh` exports it, next to `NODE_VERSION`). A build without
  it fails.
- **BREAKING** for the Python agent base image: it moves from uv
  `0.11.16` to `UV_VERSION` (`0.12.23`). The pin wins over the drifted
  tag. The image tag suffix `python3.13-trixie-slim` stays a literal.
  It is not a pin.
- Extend `task versions:check` with one function per pin. A literal Helm
  version, a numeric uv tag, an npm lockfile whose openspec or renovate
  version disagrees, or an OpenSpec skill `generatedBy` that disagrees,
  fails the check.
- actionlint, bats, shellcheck, shfmt, and task have no install outside
  `scripts/setup.sh` and `scripts/lib/assets.sh`. The check fails if a
  workflow or Dockerfile gains an install of one of them, at any
  version.
- Refresh the uv image digest in the same Renovate pull request that
  bumps `UV_VERSION`, and regenerate the OpenSpec skill stamps in the
  one that bumps `OPENSPEC_VERSION`.
- The `v` prefix examples in the pinned-tool-versions rule stop
  embedding the live shfmt and task versions.

## Capabilities

### New Capabilities

### Modified Capabilities

- `repo-tooling`: every pin in `scripts/lib/versions.sh` is the only
  copy of that tool, `versions:check` enforces that, and a
  `UV_VERSION` bump refreshes the Python agent base image digest.

## Impact

- Images: `docker/Dockerfile.python-agent`. Compose services that build
  it, in corto, lungo, and recruiter.
- Workflows: `.github/workflows/docker-build-reusable.yaml`,
  `.github/workflows/helm-package-reusable.yaml`,
  `.github/workflows/renovate.yaml`.
- Toolchain: `scripts/env.sh`, a digest record under `scripts/lib/`, a
  generator under `scripts/tools/`, `renovate.json`. Renovate must not
  rewrite the uv `FROM` line into a number, and must keep updating the
  dir-ctl and dir-mcp lines in the same Dockerfile.
- Docs: the UI and agent `docker/README.*.md` build examples, the
  version-sync rule, and the pinned-tool-versions examples.
- `sync-node-version` is complete and not archived. Its requirement that
  `versions:check` ignore every non-Node pin is replaced here. Archive
  that change first.
