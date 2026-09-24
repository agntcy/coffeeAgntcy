# GitHub Workflows

This directory contains CI/CD workflows for building images, packaging Helm charts, running integration tests, and publishing documentation.

## Overview

| Workflow | Purpose | Triggers |
|----------|---------|----------|
| [`ci-gate.yaml`](ci-gate.yaml) | Required status check: lints every workflow file (actionlint) and waits for/reports on every sibling workflow run on the same commit, including startup failures | pull_request, push (main, tags), workflow_dispatch |
| [`docker-build-push.yaml`](docker-build-push.yaml) | Build multi-arch Docker images for all agents and optionally push to GHCR, guarded against overwriting an existing tag | push (main, tags), pull_request (paths filter), workflow_dispatch |
| [`docker-build-reusable.yaml`](docker-build-reusable.yaml) | Reusable job: build and push a single Docker image | workflow_call |
| [`docs.yaml`](docs.yaml) | Publish MkDocs site to GitHub Pages (gh-pages) | push (main, README.md path) |
| [`fe-ci.yaml`](fe-ci.yaml) | Typecheck, ESLint, and Prettier for the Lungo frontend | push (main, frontend paths), pull_request (main, frontend paths) |
| [`helm-package-reusable.yaml`](helm-package-reusable.yaml) | Reusable job: lint, package, and push a single Helm chart | workflow_call |
| [`helm-push.yaml`](helm-push.yaml) | Lint, package, and (on push to main only) push changed Helm charts to GHCR (OCI), guarded against overwriting an existing chart version | push (main, tags), pull_request (paths filter), workflow_dispatch |
| [`python-lint.yaml`](python-lint.yaml) | Run `ruff check` (lint only, never reformats) for corto, lungo, recruiter | pull_request (paths filter), push (main, paths filter), workflow_dispatch |
| [`scorecard.yaml`](scorecard.yaml) | OpenSSF Scorecard security analysis, uploads SARIF to code scanning | push (main), pull_request, schedule (weekly), workflow_dispatch |
| [`source-lint.yaml`](source-lint.yaml) | Forbidden strings check (fails if an en dash or em dash appears anywhere in the repo) and Helm chart version-bump check (fails if a chart's contents changed since the last release tag without a `Chart.yaml` version bump) | pull_request, push (main), workflow_dispatch |
| [`test-reusable.yaml`](test-reusable.yaml) | Reusable job: run pytest for one project directory and path set | workflow_call |
| [`test-subprojects-reusable.yaml`](test-subprojects-reusable.yaml) | Path-filter job: which agent projects changed | workflow_call |
| [`test.yaml`](test.yaml) | Run pytest for corto, lungo, recruiter | push (main), pull_request, workflow_call, workflow_dispatch |
| [`version-override-test.yaml`](version-override-test.yaml) | Example invocation of reusable tests with dependency/image overrides | workflow_dispatch |

## ci-gate

Single required status check for the repo, self-contained in one file with no manual list of other workflows to maintain:

1. **Validate** - runs `actionlint` (via `reviewdog/action-actionlint`) against every file under `.github/workflows/` on the checked-out commit, catching schema/syntax/structure issues and shellcheck findings in `run:` scripts. Always runs to completion (`continue-on-error: true`) so it never short-circuits step 2.
2. **Wait** - since there's no native way for one workflow to block another from starting, this polls `GET /actions/runs?head_sha=...` (the runs API, not the checks API - the checks API silently omits `startup_failure` runs) every minute, after an initial one-minute settle delay, until nothing else for that commit is left `queued`/`in_progress` for two consecutive polls, or 100 minutes elapse.
3. **Summarize** - always runs regardless of steps 1-2's outcome, writes a table to the job summary (validation result + every sibling run's name/conclusion/link, including anything still pending at timeout), and only then decides pass/fail: `success`/`skipped` count as pass, everything else (`failure`, `startup_failure`, `cancelled`, `timed_out`, `neutral`, or still-pending-at-timeout) counts as fail.

For this to actually gate merges, `CI Gate` needs to be added as a `required_status_checks` context in the branch ruleset (currently managed in `agntcy/org-admin`'s `safe-settings/repos/coffeeAgntcy.yml`, which as of this writing has no `required_status_checks` rule at all).

## docker-build-push

Matrix builds all defined images (see matrix.image array). The push target depends on the triggering event:

- `pull_request`: build only, no push (tag `pr-<PR_NUMBER>`).
- push to `main`: push, tag `latest`.
- push of a git tag: push, tag = the git tag name.
- `workflow_dispatch`: push only if the `push` input is set; tag = the `image_tag` input, or an auto-generated `dispatch_<sha>_run-<run_number>` tag if left blank.

Before any of the above pushes, `check-push-target-existence` looks up whether an image with that exact tag already exists in GHCR and fails the workflow if so, so a push never silently overwrites a previously published tag. The floating `latest` tag is exempt from this check by design. If you need to retry after a bad push (e.g. a tag reused by mistake), manually delete the conflicting version from GHCR first.

Key build args (`BUILD_VERSION`, `BUILD_DATE`, `GIT_COMMIT_SHORT`, etc.) and OCI labels supply provenance. Update the matrix to add/remove images:

```yaml
strategy:
  matrix:
    image:
      - name: new-component
        dockerfile: coffeeAGNTCY/coffee_agents/.../docker/Dockerfile.new
```

Ensure the Dockerfile path is correct and the name is unique under `ghcr.io/<org>/coffee-agntcy/`.

Also add the new image's name to the matching `{CORTO,LUNGO,RECRUITER}_IMAGES_JSON` list in the workflow's `env:` block - `check-push-target-existence` reads image names from there, separately from the matrix above, and won't guard an image it doesn't list.

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

The job has `timeout-minutes: 90` - historically, hung builds here ran to GitHub's default 6-hour job ceiling before being force-cancelled; 90 minutes gives comfortable headroom over the longest legitimate run (~28 min) while failing fast on a genuine hang.

## helm-push

Packages each chart listed in `CORTO_CHARTS_JSON`/`LUNGO_CHARTS_JSON` (the workflow's `env:` block) - the single source of truth for chart paths and package names, shared by the matrices and by the guard logic below. Charts are pushed to `ghcr.io/<org>/coffee_agntcy/helm` as OCI artifacts **only** on a push to `main`; a git tag push never pushes charts (Helm charts are not tied to git tags - see [`docs/RELEASE-OPS.md`](../../docs/RELEASE-OPS.md)), and PRs only lint and package.

Two guards run before any chart is pushed on a push to `main`:

- **Unchanged charts are dropped from the matrix before packaging starts.** Repackaging a chart whose directory has no content changes since the previous commit on `main` still produces a different `.tgz` (timestamps are baked into the archive), which would otherwise silently overwrite an existing, supposedly-immutable published version.
- **`check-push-target-existence`** looks up whether the chart's `Chart.yaml` `version:` already exists as a published tag in GHCR and fails the workflow if so. This is what enforces the rule that any chart content change must come with a version bump (see `docs/RELEASE-OPS.md`, Step 0). If you need to retry after a bad push, manually delete the conflicting version from GHCR first.

To add a chart, add an entry to both `CORTO_CHARTS_JSON`/`LUNGO_CHARTS_JSON` in `helm-push.yaml`'s `env:` block:

```json
{"package_name": "my-service", "path": "coffeeAGNTCY/coffee_agents/.../deployment/helm/my-service"}
```

Chart version is taken from `Chart.yaml` (`version` field). Bump that value to publish a new artifact.

## helm-package-reusable

Reusable workflow called by `helm-push.yaml` for each matrix entry. Accepts:

| Input | Description |
|-------|-------------|
| `path` | Path to the chart directory (required) |
| `package_name` | Package name for the chart (required) |
| `push` | Whether to push to GHCR OCI registry (default: false) |

The job has `timeout-minutes: 90`, for the same reason as `docker-build-reusable` (longest legitimate run here is ~53 min).

## test (Python Tests)

Orchestrates pytest for each changed agent project (`corto`, `lungo`, `recruiter`) via `test-reusable.yaml`. Also exposed as a reusable workflow with optional dependency and Docker image overrides.

### Concurrency

**`tests / *`** jobs cancel in-progress runs on new pushes (`cancel-in-progress: true`).

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
| `test_paths` | Space-separated pytest directory arguments and flags, e.g. `tests --ignore=tests/integration/llm` (required) |
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

Demonstrates how to pin or constrain dependencies and override container images when calling the reusable test workflow.

## docs

Deploys with MkDocs Material to `gh-pages` when `README.md` is updated on main. Ensure `mkdocs.yml` exists at repo root and GitHub Pages is configured to serve the `gh-pages` branch.
