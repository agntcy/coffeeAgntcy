# GitHub Workflows

This directory contains CI/CD workflows for building images, packaging Helm charts, running integration tests, and publishing documentation.

## Overview

| Workflow | Purpose | Triggers |
|----------|---------|----------|
| [`docker-build-push.yaml`](.github/workflows/docker-build-push.yaml) | Build multi-arch Docker images for all agents and optionally push to GHCR | push (main, tags), pull_request (main), workflow_dispatch |
| [`helm-push.yaml`](.github/workflows/helm-push.yaml) | Lint, package, and (on push to main) push Helm charts to GHCR (OCI) | push (main), pull_request (main), workflow_dispatch |
| [`test.yaml`](.github/workflows/test.yaml) | Integration test matrix (corto, lungo) exposed as reusable workflow | pull_request (main), push (main), workflow_call |
| [`version-override-test.yaml`](.github/workflows/version-override-test.yaml) | Example invocation of reusable tests with dependency/image overrides | workflow_dispatch |
| [`docs.yaml`](.github/workflows/docs.yaml) | Publish MkDocs site to GitHub Pages (gh-pages) | push (main) |

## docker-build-push

Matrix builds all defined images (see matrix.image array). PRs build (no push) with tag pr-<PR_NUMBER>. Main pushes publish :latest. Git tags publish the tag as image tag.

Key build args (BUILD_VERSION, BUILD_DATE, GIT_COMMIT_SHORT, etc.) and OCI labels supply provenance. Update the matrix to add/remove images:

```yaml
strategy:
  matrix:
    image:
      - name: new-component
        dockerfile: coffeeAGNTCY/coffee_agents/.../docker/Dockerfile.new
```

Ensure Dockerfile path is correct and name unique under ghcr.io/<org>/coffee-agntcy/.

## helm-push

Packages each chart listed under matrix.chart. On push to main charts are pushed to ghcr.io/<org>/coffee_agntcy/helm as OCI artifacts; PRs only lint + package.

To add a chart:

```yaml
- name: my-service
  path: coffeeAGNTCY/coffee_agents/.../deployment/helm/my-service
  package_name: my-service
```

Chart version is taken from Chart.yaml (version field). Bump that value to publish a new artifact.

## test (reusable)

Provides integration test execution via uv for suites (currently corto and lungo). Exposes inputs for dependency and Docker image overrides.

Inputs:

| Input | Description |
|-------|-------------|
| pip_overrides | PEP 508 specs (one per line) forced into the lock (e.g. httpx==0.27.2) |
| pip_constraints | Constraint lines applied during resolution (e.g. grpcio<1.65) |
| docker_overrides | Lines service=image[:tag] to patch docker-compose service images |

Example caller (see version-override-test):

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
        slim=ghcr.io/agntcy/slim:0.5.0
```

## version-override-test

Demonstrates how to pin or constrain dependencies and override container images when calling the reusable test workflow.

## docs

Copies top-level docs (README, CONTRIBUTING, etc.) into docs/ then deploys with MkDocs Material to gh-pages. Ensure mkdocs.yml exists at repo root (or adapt the workflow) and GitHub Pages is configured to serve gh-pages.
