# Design

## Context

See proposal.md for motivation. The check follows the repo's standard
five-layer pipeline (see `.agents/rules/meta/repo-operation-pipeline.md`)
and is modelled on `locks:check` / `check_uv_locks.bash`: it never
rewrites a committed file and resolves its tool via `.tools/bin` first.

## Goals / Non-Goals

**Goals:**
- Detect any Chart.lock that `helm dependency update` would change, for
  third-party and `file://` sibling dependencies alike, plus a missing lock.
- Give the failure a local fix command, `task helm:update-locks`.
- Keep helm pinned and repo-local like every other tool.

**Non-Goals:**
- **Offline operation.** Resolving OCI and https dependencies needs the
  network. Accepted, as `locks:check` makes the same trade for Python.
- **Checking version-bump policy for lock changes.** `helm:check-versions`
  already requires a bump for any chart content change, `Chart.lock`
  included; this change only cross-references it.
- **Pinning loose constraints.** A non-exact dependency constraint could
  resolve to newer versions over time and make the check flaky. Every
  dependency in the repo is pinned exactly today; making that a rule is out
  of scope.

## Decisions

**Re-run `helm dependency update` in a scratch copy, then diff the lock.**
Three cheaper options were tried against the real pre-fix corto state:

- `helm dependency list` reports every dependency as `missing` for the
  broken and the fixed state alike, because it only compares `Chart.yaml`
  with an uncommitted `charts/` directory. Rejected: it catches nothing.
- `helm dependency build --skip-refresh` detects a lock whose digest no
  longer matches `Chart.yaml`, but when the digest matches it goes on to
  download every chart, and it would not catch a sibling pin that agrees
  with the lock yet not with the sibling's own version. Rejected as both
  incomplete and no cheaper than the update.
- Parsing `Chart.yaml` and `Chart.lock` by hand (name, version,
  repository, sibling versions). Rejected: it approximates helm's own
  resolver, needs a YAML parser the toolchain lacks, and misses whatever
  the approximation forgets.

Running the real operation catches everything it would change or fail on.
Against the real repo it reproduces both committed locks exactly in about
7 seconds per chart; against the pre-fix corto state it fails with the same
`can't get a valid version for 3 subchart(s)` error Renovate hit.

**One updater, two callers.** `update_chart_locks.bash [root-dir]` is the
generative operation and takes an optional root. The check copies every
tracked file of every chart directory into a temp tree (siblings resolve
relative to each other, so all must be present) and calls the updater on
it, then diffs, ignoring `generated:`. The committed tree is never touched.

**Isolated helm state.** `HELM_CACHE_HOME`, `HELM_CONFIG_HOME`, and
`HELM_DATA_HOME` default to `.tools/helm/...` unless the caller set them,
keeping the toolchain's "nothing outside the repo" property. helm's
`dependency update` needs no `helm repo add` for https repositories
declared in `Chart.yaml`, verified empirically.

**Downloaded `charts/` is removed afterwards**, unless it existed before
the run, since it is build output and not gitignored.

**helm installs unconditionally**, not behind `--lint-only`, for the same
reason uv and bats do: the check runs in CI's `task check:all`.

**Version pin: `v4.3.0`**, the release already on the maintainer's
machine, from `get.helm.sh`, tracked by Renovate via
`datasource=github-releases depName=helm/helm`.

## Risks / Trade-offs

- **Registry rate limits.** Anonymous Docker Hub pulls
  (`registry-1.docker.io/bitnamicharts`) from shared CI runners could be
  throttled and make the check flaky. Mitigation if it happens: retry, or
  authenticate the registry.
- **Check duration.** About 16 seconds for today's two umbrella charts,
  running in parallel with the other checks, so it is not on the critical
  path.
- **Helm major version.** helm 4 and 3 write the same lock format today;
  a future format change would show up as a diff on the first check after a
  pin bump, which is the intended signal.
