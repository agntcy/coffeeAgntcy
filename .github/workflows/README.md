# GitHub Workflows

This directory contains CI/CD workflows for building images, packaging Helm charts, running integration tests, and publishing documentation.

## Overview

| Workflow | Purpose | Triggers |
|----------|---------|----------|
| [`docker-build-push.yaml`](.github/workflows/docker-build-push.yaml) | Build multi-arch Docker images for all agents and optionally push to GHCR | push (main, tags), pull_request (paths filter), workflow_dispatch |
| [`docker-build-reusable.yaml`](.github/workflows/docker-build-reusable.yaml) | Reusable job: build and push a single Docker image | workflow_call |
| [`helm-push.yaml`](.github/workflows/helm-push.yaml) | Lint, package, and (on push to main/tags) push Helm charts to GHCR (OCI) | push (main, tags), pull_request (paths filter), workflow_dispatch |
| [`helm-package-reusable.yaml`](.github/workflows/helm-package-reusable.yaml) | Reusable job: lint, package, and push a single Helm chart | workflow_call |
| [`test.yaml`](.github/workflows/test.yaml) | Directory-based no-secrets pytest for corto, lungo, recruiter | push (main), pull_request, workflow_call, workflow_dispatch |
| [`test-reusable.yaml`](.github/workflows/test-reusable.yaml) | Reusable job: run pytest for one project directory and path set | workflow_call |
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

Runs directory-based **no-secrets** pytest for each changed agent project. Check names in the PR UI: **`tests / corto`**, **`tests / lungo`**, **`tests / recruiter`**.

LLM tests live under `tests/integration_llm/` and are **local-only** (not run in CI) until project leadership re-enables them.

### Test directories

| Directory | Meaning | CI |
|-----------|---------|-----|
| `tests/unit/` | Mocks only | Yes |
| `tests/live/` | Subprocess uvicorn/A2A (lungo only) | Yes |
| `tests/integration/` | Docker-compose session; no LLM | Yes |
| `tests/integration_llm/` | Docker + LLM credentials | No (local manual) |

### Per-project CI pytest paths

| Project | `test_paths` |
|---------|--------------|
| corto | `tests/unit tests/integration` |
| lungo | `tests/unit tests/live tests/integration` |
| recruiter | `tests/unit tests/integration` |

CI always passes explicit paths (never bare `pytest`, which would collect `integration_llm/` via `testpaths = ["tests"]`).

The reusable job sets `WORKFLOW_API_KEY` for lungo live tests (not a repository secret).

Local commands:

```bash
# CI-equivalent (no secrets)
cd coffeeAGNTCY/coffee_agents/corto && uv run pytest tests/unit tests/integration -q
cd coffeeAGNTCY/coffee_agents/lungo && uv run pytest tests/unit tests/live tests/integration -q
cd coffeeAGNTCY/coffee_agents/recruiter && uv run pytest tests/unit tests/integration -q

# LLM (local only, needs .env)
cd coffeeAGNTCY/coffee_agents/lungo && uv run pytest tests/integration_llm -q
```

Do not run `pytest tests/` as a single full-suite invocation when both `integration/` and `integration_llm/` exist — session fixtures may load twice via `pytest_plugins`.

### Branch protection

| Remove (legacy) | Add (required on PRs) |
|-----------------|----------------------|
| `integration-tests-*` | `tests / *` |
| `fast / *`, `integration / *` | `tests / *` |

### Concurrency

**`tests / *`** jobs cancel in-progress runs on new pushes (`cancel-in-progress: true`).

### Re-enabling LLM CI (future)

When policy allows, add a separate workflow job that runs `pytest tests/integration_llm` with secrets on trusted triggers. The directory layout is already in place.

### workflow_call inputs

| Input | Description |
|-------|-------------|
| `test_corto`, `test_lungo`, `test_recruiter` | Subproject toggles (workflow_call / dispatch only) |
| `pip_overrides`, `pip_constraints`, `docker_overrides` | Dependency and image overrides |

## test-reusable

Runs `pytest` via `uv` for a single project directory and explicit path list.

| Input | Description |
|-------|-------------|
| `project_dir` | Path to the project directory to test (required) |
| `test_paths` | Space-separated pytest paths, e.g. `tests/unit tests/integration` (required) |
| `pip_overrides` | PEP 508 specs (one per line) forced into the lock |
| `pip_constraints` | Constraint lines applied during resolution |
| `docker_overrides` | Lines `service=image[:tag]` to patch docker-compose service images |

Example caller (see `version-override-test.yaml`):

```yaml
jobs:
  integration:
    uses: <org>/<repo>/.github/workflows/test.yaml@<ref>
    with:
      pip_overrides: |
        httpx==0.27.2
      pip_constraints: |
        grpcio<1.65
      docker_overrides: |
        slim=ghcr.io/agntcy/slim:1.4.0
```

## fe-ci

Runs frontend checks (TypeScript typecheck, ESLint, Prettier via `npm run check`) for the Lungo frontend. Only triggers when files under `coffeeAGNTCY/coffee_agents/lungo/frontend/` change.

## version-override-test

Demonstrates how to pin or constrain dependencies and override container images when calling the reusable test workflow. Runs the no-secrets directory suites only (no LLM tests in CI).

## docs

Deploys with MkDocs Material to `gh-pages` when `README.md` is updated on main. Ensure `mkdocs.yml` exists at repo root and GitHub Pages is configured to serve the `gh-pages` branch.
