# GitHub Workflows

This directory contains CI/CD workflows for building images, packaging Helm charts, running integration tests, and publishing documentation.

## Overview

| Workflow | Purpose | Triggers |
|----------|---------|----------|
| [`docker-build-push.yaml`](.github/workflows/docker-build-push.yaml) | Build multi-arch Docker images for all agents and optionally push to GHCR | push (main, tags), pull_request (paths filter), workflow_dispatch |
| [`docker-build-reusable.yaml`](.github/workflows/docker-build-reusable.yaml) | Reusable job: build and push a single Docker image | workflow_call |
| [`helm-push.yaml`](.github/workflows/helm-push.yaml) | Lint, package, and (on push to main/tags) push Helm charts to GHCR (OCI) | push (main, tags), pull_request (paths filter), workflow_dispatch |
| [`helm-package-reusable.yaml`](.github/workflows/helm-package-reusable.yaml) | Reusable job: lint, package, and push a single Helm chart | workflow_call |
| [`test.yaml`](.github/workflows/test.yaml) | Orchestrate integration tests across projects | push (main, corto paths), pull_request, workflow_call, workflow_dispatch |
| [`test-reusable.yaml`](.github/workflows/test-reusable.yaml) | Reusable job: run integration tests for a single project directory | workflow_call |
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

## test

Orchestrates integration tests by calling `test-reusable.yaml` for each project (currently corto and lungo). Also exposed as a reusable workflow and accepts overrides for dependencies and Docker images.

## test-reusable

Reusable job that runs `pytest` via `uv` for a single project directory. Exposes inputs for dependency and Docker image overrides.

Inputs:

| Input | Description |
|-------|-------------|
| `project_dir` | Path to the project directory to test (required) |
| `pip_overrides` | PEP 508 specs (one per line) forced into the lock (e.g. `httpx==0.27.2`) |
| `pip_constraints` | Constraint lines applied during resolution (e.g. `grpcio<1.65`) |
| `docker_overrides` | Lines `service=image[:tag]` to patch docker-compose service images |

Example caller (see `version-override-test.yaml`):

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

## fe-ci

Runs frontend checks (TypeScript typecheck, ESLint, Prettier via `npm run check`) for the Lungo frontend. Only triggers when files under `coffeeAGNTCY/coffee_agents/lungo/frontend/` change.

## version-override-test

Demonstrates how to pin or constrain dependencies and override container images when calling the reusable test workflow.

## docs

Deploys with MkDocs Material to `gh-pages` when `README.md` is updated on main. Ensure `mkdocs.yml` exists at repo root and GitHub Pages is configured to serve the `gh-pages` branch.
