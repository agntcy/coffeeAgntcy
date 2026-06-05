# GitHub Workflows

This directory contains CI/CD workflows for building images, packaging Helm charts, running integration tests, and publishing documentation.

## Overview

| Workflow | Purpose | Triggers |
|----------|---------|----------|
| [`fe-ci.yaml`](fe-ci.yaml) | Lungo frontend typecheck, ESLint, Prettier (no secrets) | pull_request, push (main), `lungo/frontend/**` paths |
| [`ci-smoke.yaml`](ci-smoke.yaml) | Python smoke tests (`tests/unit` / collect-only; no secrets) | pull_request, push (main), agent paths |
| [`test.yaml`](test.yaml) | **Mandatory** Python integration (`integration / *`, LLM secrets) | Same-repo PR, push (main), `workflow_call`, `workflow_dispatch` |
| [`integration-fork-approve.yaml`](integration-fork-approve.yaml) | **Mandatory** integration for fork PRs (same `integration / *` checks; runs after team **Approve**) | `pull_request_review` submitted |
| [`docker-build-push.yaml`](docker-build-push.yaml) | Build multi-arch Docker images for all agents and optionally push to GHCR | push (main, tags), pull_request (main), workflow_dispatch |
| [`helm-push.yaml`](helm-push.yaml) | Lint, package, and (on push to main) push Helm charts to GHCR (OCI) | push (main), pull_request (main), workflow_dispatch |
| [`version-override-test.yaml`](version-override-test.yaml) | Example invocation of reusable tests with dependency/image overrides | workflow_dispatch |
| [`docs.yaml`](docs.yaml) | Publish MkDocs site to GitHub Pages (gh-pages) | push (main) |

## Python CI lanes (smoke vs integration)

**Integration tests are mandatory for every PR** that touches agent paths (enforced via branch protection). Smoke runs on every push; integration uses LLM secrets and must be green before merge.

| Lane | Workflow | Required to merge? | When it runs |
|------|----------|-------------------|--------------|
| Smoke | [`ci-smoke.yaml`](ci-smoke.yaml) | Yes (path-scoped) | Every PR/push (no secrets) |
| Integration | [`test.yaml`](test.yaml) or [`integration-fork-approve.yaml`](integration-fork-approve.yaml) | **Yes** — `integration / corto`, `integration / lungo`, `integration / recruiter` (per changed project) | Same-repo: auto on each push. **Fork:** only after **Approve** from [`@agntcy/coffee-agntcy-reviewers`](https://github.com/orgs/agntcy/teams/coffee-agntcy-reviewers) (one run per `head.sha`, deduped). New fork commits need a new approve before integration runs again. |

Both integration entry points call the same [`test-reusable.yaml`](test-reusable.yaml) jobs with the same check names (`integration / *`), so branch protection can list those checks once for all contributors.

When path filters exclude a project, a lightweight **path-skip** job still reports success under the same check name (for example `integration / lungo`). That satisfies required checks without running tests. Skips for other reasons (fork PRs before team approve, cancelled runs, and similar) do not get a passing path-skip job.

Reusable workflows: [`test-subprojects-reusable.yaml`](test-subprojects-reusable.yaml) (path filters), [`test-smoke-reusable.yaml`](test-smoke-reusable.yaml), [`test-reusable.yaml`](test-reusable.yaml) (integration).

### Branch protection (admin)

On `main`, require (copy exact names from the PR Checks tab after one run):

- **smoke /*** — for Python agent changes
- **integration /*** — for Python agent changes (mandatory for same-repo and fork PRs)
- **FE CI** / `frontend-build` — when `lungo/frontend/**` changes

Fork PRs will show integration checks as pending until a team reviewer **Approves** and the workflow completes; merge stays blocked until those checks succeed.

### Secrets and tokens

- **LLM / Azure** (`LLM_MODEL`, `AZURE_*`): repo secrets; used only by integration workflows.
- **`GH_TOKEN`** (repo secret): fork-approve **gate** only — org team membership (`read:org`) and Actions dedupe (`actions: read`). Default `GITHUB_TOKEN` cannot read org teams.

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

## ci-smoke

Runs secret-free smoke tests per changed agent project:

| Project | Command |
|---------|---------|
| lungo | `pytest tests/unit -m "not e2e"` |
| corto | `pytest tests/unit` |
| recruiter | `pytest tests/ --collect-only` |

Check names in the PR UI: `smoke / lungo`, `smoke / corto`, `smoke / recruiter`.

## test (integration)

Mandatory LLM-backed integration via uv for corto, lungo, and recruiter (`tests/integration` only). Check names: **`integration / corto`**, **`integration / lungo`**, **`integration / recruiter`** (path-scoped).

- **Same-repo PRs:** [`test.yaml`](test.yaml) runs these jobs on each push.
- **Fork PRs:** [`test.yaml`](test.yaml) does not run on fork `pull_request` (no secrets on that event). The same checks are produced by [`integration-fork-approve.yaml`](integration-fork-approve.yaml) after a team **Approve**.

Exposes inputs for dependency and Docker image overrides.

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
