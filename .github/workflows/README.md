# GitHub Workflows

This directory contains CI/CD workflows for building images, packaging Helm charts, running integration tests, and publishing documentation.

## Overview

| Workflow | Purpose | Triggers |
|----------|---------|----------|
| [`docker-build-push.yaml`](.github/workflows/docker-build-push.yaml) | Build multi-arch Docker images for all agents and optionally push to GHCR | push (main, tags), pull_request (paths filter), workflow_dispatch |
| [`docker-build-reusable.yaml`](.github/workflows/docker-build-reusable.yaml) | Reusable job: build and push a single Docker image | workflow_call |
| [`helm-push.yaml`](.github/workflows/helm-push.yaml) | Lint, package, and (on push to main/tags) push Helm charts to GHCR (OCI) | push (main, tags), pull_request (paths filter), workflow_dispatch |
| [`helm-package-reusable.yaml`](.github/workflows/helm-package-reusable.yaml) | Reusable job: lint, package, and push a single Helm chart | workflow_call |
| [`test.yaml`](.github/workflows/test.yaml) | Python test tiers (fast + integration) for corto, lungo, recruiter | push (main), pull_request, workflow_call, workflow_dispatch |
| [`test-reusable.yaml`](.github/workflows/test-reusable.yaml) | Reusable job: run pytest for one project in a given tier | workflow_call |
| [`test-subprojects-reusable.yaml`](.github/workflows/test-subprojects-reusable.yaml) | Path-filter job: which agent projects changed | workflow_call |
| [`fe-ci.yaml`](.github/workflows/fe-ci.yaml) | Typecheck, ESLint, and Prettier for the Lungo frontend | push (main, frontend paths), pull_request (main, frontend paths) |
| [`version-override-test.yaml`](.github/workflows/version-override-test.yaml) | Example invocation of reusable tests with dependency/image overrides | workflow_dispatch |
| [`docs.yaml`](.github/workflows/docs.yaml) | Publish MkDocs site to GitHub Pages (gh-pages) | push (main, README.md path) |

## docker-build-push

Matrix builds all defined images (see matrix.image array). PRs build (no push) with tag `pr-<PR_NUMBER>`. Pushes to main publish `:latest`. Git tags publish the tag as image tag.

Key build args (`BUILD_VERSION`, `BUILD_DATE`, `GIT_COMMIT_SHORT`, etc.) and OCI labels supply provenance. Update the matrix to add/remove images:

```yaml
strategy:
  matrix:
    image:
      - name: new-component
        dockerfile: coffeeAGNTCY/coffee_agents/.../docker/Dockerfile.new
```

Ensure the Dockerfile path is correct and the name is unique under `ghcr.io/<org>/coffee-agntcy/`.

## docker-build-reusable

Reusable workflow called by `docker-build-push.yaml` for each matrix entry. Accepts:

| Input | Description |
|-------|-------------|
| `name` | Container image name (required) |
| `dockerfile` | Path to Dockerfile (required) |
| `image_tag` | Tag for the container image (required) |
| `git_branch` | Branch name for provenance labels (required) |
| `push` | Whether to push to GHCR (default: false) |
| `platforms` | Target platforms (default: linux/amd64,linux/arm64) |
| `extra_build_args` | Additional newline-separated KEY=value build args (optional) |

## helm-push

Packages each chart listed under matrix.chart. On push to main or a tag, charts are pushed to `ghcr.io/<org>/coffee_agntcy/helm` as OCI artifacts; PRs only lint and package.

To add a chart:

```yaml
- name: my-service
  path: coffeeAGNTCY/coffee_agents/.../deployment/helm/my-service
  package_name: my-service
```

Chart version is taken from `Chart.yaml` (`version` field). Bump that value to publish a new artifact.

## helm-package-reusable

Reusable workflow called by `helm-push.yaml` for each matrix entry. Accepts:

| Input | Description |
|-------|-------------|
| `path` | Path to the chart directory (required) |
| `package_name` | Package name for the chart (required) |
| `push` | Whether to push to GHCR OCI registry (default: false) |

## test (Python Tests)

Runs marker-driven pytest tiers for each changed agent project. Check names in the PR UI: **`fast / corto`**, **`fast / lungo`**, **`fast / recruiter`**, **`integration / corto`**, etc.

### Pytest markers

| Marker | Meaning |
|--------|---------|
| *(none)* | Pure unit — mocks only |
| `live_server` | Subprocess uvicorn/A2A HTTP |
| `docker` | Requires docker-compose session (auto-applied under `tests/integration/`) |
| `llm` | Requires live LiteLLM/Azure credentials |

### CI tiers

| Job | Pytest selection | Secrets | Docker |
|-----|------------------|---------|--------|
| **fast / *** | `-m "not llm and not docker"` | No | No |
| **integration / *** (fork PR) | `-m "docker and not llm"` | No | Yes |
| **integration / *** (same-repo) | `-m "llm or (docker and not llm)"` | Yes | Yes — single pytest session |

Fork PRs skip LLM tests (no `.env` written). Same-repo branches run the full integration selection in one pytest invocation.

Local commands:

```bash
uv run pytest -m "not llm and not docker" -q   # fast tier
uv run pytest -m "docker and not llm" -q       # docker tier
uv run pytest -m "llm" -q                     # LLM tier (needs .env)
```

### Branch protection

Replace legacy required checks with the new tier job names:

| Remove (legacy) | Add (required) |
|-----------------|----------------|
| `integration-tests-corto` | `fast / corto`, `integration / corto` |
| `integration-tests-lungo` | `fast / lungo`, `integration / lungo` |
| `integration-tests-recruiter` | `fast / recruiter`, `integration / recruiter` |

Require **`fast / *`** and **`integration / *`** for agent path changes. Fork PRs can satisfy both without LLM secrets.

### Concurrency

**Fast** jobs cancel in-progress runs on new pushes (`cancel-in-progress: true`). **Integration** jobs are not cancelled mid-run.

Fork detection is computed in `test.yaml` and passed to `test-reusable.yaml` as `fork_pr` (reusable workflows do not reliably inherit PR fork context).

### workflow_call inputs

| Input | Description |
|-------|-------------|
| `test_mode` | `all` (default), `fast`, `integration`, or `llm-only` |
| `test_corto`, `test_lungo`, `test_recruiter` | Subproject toggles (workflow_call / dispatch only) |
| `pip_overrides`, `pip_constraints`, `docker_overrides` | Dependency and image overrides |

## test-reusable

Runs `pytest` via `uv` for a single project directory in **`fast`**, **`integration`**, or **`llm-only`** mode.

| Input | Description |
|-------|-------------|
| `project_dir` | Path to the project directory to test (required) |
| `test_mode` | `fast` \| `integration` \| `llm-only` (required) |
| `fork_pr` | Set by `test.yaml` when the PR head repo is a fork; skips `.env` and LLM marker selection |
| `pip_overrides` | PEP 508 specs (one per line) forced into the lock |
| `pip_constraints` | Constraint lines applied during resolution |
| `docker_overrides` | Lines `service=image[:tag]` to patch docker-compose service images |

Example caller (see `version-override-test.yaml`; `test_mode` defaults to `all`):

```yaml
jobs:
  integration:
    uses: <org>/<repo>/.github/workflows/test.yaml@<ref>
    secrets: inherit
    with:
      pip_overrides: |
        httpx==0.27.2
      pip_constraints: |
        grpcio<1.65
      docker_overrides: |
        slim=ghcr.io/agntcy/slim:1.4.0
```

Use `test_mode: llm-only` only when you intentionally want to skip fast and docker-only integration tests.

## fe-ci

Runs frontend checks (TypeScript typecheck, ESLint, Prettier via `npm run check`) for the Lungo frontend. Only triggers when files under `coffeeAGNTCY/coffee_agents/lungo/frontend/` change.

## version-override-test

Demonstrates how to pin or constrain dependencies and override container images when calling the reusable test workflow. Uses the default `test_mode: all` so fast, docker, and LLM tiers all run against the overridden images.

## docs

Deploys with MkDocs Material to `gh-pages` when `README.md` is updated on main. Ensure `mkdocs.yml` exists at repo root and GitHub Pages is configured to serve the `gh-pages` branch.
