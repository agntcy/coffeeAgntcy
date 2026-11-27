# Proposal

## Why

`NODE_VERSION` in `scripts/lib/versions.sh` is already the pin for the
local toolchain, and `scripts/setup.sh` installs that exact Node into
`.tools/node`. The other places that install Node do not read it. Frontend
CI hardcodes `node-version`, and `docker/Dockerfile.ui` hardcodes the
`node` image tag. Renovate bumps those copies in different groups from
the pin, so they can drift. Nothing fails when they do.

## What Changes

- Make every current Node install read `NODE_VERSION`: local setup (already
  does), frontend CI, and the UI image build (`Dockerfile.ui`, used by the
  corto and lungo UI services).
- Add one standing check, one script with one function for Node, that fails
  when an install does not use that variable or when a literal that cannot
  source it (the UI image digest, the frontend `engines.node` floor) does
  not match it.
- Refresh the UI image digest in the same Renovate pull request that bumps
  `NODE_VERSION`, the same way archive checksums are refreshed today.
- **BREAKING** for local UI image builds: `docker compose` and the
  documented `docker build` lines require `NODE_VERSION` in the
  environment (`source scripts/env.sh` exports it). A build without it
  fails instead of silently using a tag baked into the Dockerfile.

## Capabilities

### New Capabilities

### Modified Capabilities

- `repo-tooling`: Node installs read `NODE_VERSION`, a standing check
  enforces that, and a `NODE_VERSION` bump refreshes the UI image digest
  alongside the existing checksum and npm-lock refresh.

## Impact

- Workflows: `.github/workflows/fe-ci.yaml`,
  `.github/workflows/docker-build-reusable.yaml`,
  `.github/workflows/docker-build-push.yaml` (UI build-args only),
  `.github/workflows/renovate.yaml` (allowed post-upgrade command).
- Images: `docker/Dockerfile.ui`. Compose UI services in
  `coffeeAGNTCY/coffee_agents/{corto,lungo}/docker-compose.yaml`.
- Toolchain: `scripts/env.sh`, a new digest pin file under `scripts/lib/`,
  a new generator under `scripts/tools/`, `renovate.json` post-upgrade
  tasks.
- App manifests: both frontend `package.json` `engines.node` floors stay
  literals and must equal `>=` plus `NODE_VERSION`. `engine-strict=true`
  already rejects an older Node at `npm ci`.
- Docs that tell a person which Node to install: `TUTORIAL.md`, the corto
  and lungo READMEs, both frontend READMEs, and the UI `docker build`
  examples in `docker/README.corto.md` and `docker/README.lungo.md`.
- New check on the five-layer path (`versions:check` inside
  `task check:all`). The count of checks in
  `.agents/rules/always-apply/pre-finalize-checks.md` goes from twelve to
  thirteen.
- Python agent images (`docker/Dockerfile.python-agent`) do not install
  Node and are not given a Node install. The check only fails if one of
  them starts installing a Node other than `NODE_VERSION`.
- Other pins in `versions.sh` (uv, Helm, and the rest) are out of scope.
  `Dockerfile.python-agent` is still uv `0.11.16` while `UV_VERSION` is
  `0.12.23`. The script is shaped so a later change can add one function
  per pin.
