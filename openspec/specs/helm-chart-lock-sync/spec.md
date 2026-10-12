# helm-chart-lock-sync Specification

## Purpose
Requires every Helm chart that declares dependencies to have a committed
`Chart.lock` that `helm dependency update` reproduces, covering third-party
and `file://` sibling dependencies, and provides the operation that
regenerates it.

## Requirements

### Requirement: A chart's committed lock reproduces under `helm dependency update`
For every git-tracked Helm chart whose `Chart.yaml` declares
`dependencies:`, the check SHALL re-run `helm dependency update` in a
scratch copy of every tracked chart directory and SHALL flag the chart when
the regenerated `Chart.lock` differs from the committed one, ignoring the
`generated:` timestamp line. It SHALL flag a chart that declares
dependencies and has no committed `Chart.lock`. It SHALL NOT modify any
committed file.

#### Scenario: A third-party dependency was re-pinned without refreshing the lock
- **WHEN** a chart's `Chart.yaml` dependency version is changed and its
  `Chart.lock` is not
- **THEN** the chart is flagged as out of sync, with a diff, and the
  message names `task helm:update-locks` as the fix

#### Scenario: A sibling chart was bumped but the umbrella pin was not
- **WHEN** a chart depends on `file://../sibling` at an exact version and
  the sibling's own `version:` has since changed
- **THEN** `helm dependency update` fails to resolve it, and the check
  fails with the helm error and a note that the pin likely no longer
  matches the sibling's version

#### Scenario: A chart with dependencies has no lock
- **WHEN** a tracked chart declares dependencies and no `Chart.lock`
  exists next to it
- **THEN** the chart is flagged as having no lock

#### Scenario: Locks are in sync
- **WHEN** every dependency-declaring chart's committed `Chart.lock`
  matches the regenerated one apart from the `generated:` line
- **THEN** the check passes

### Requirement: Charts without dependencies and untracked charts are ignored
The check SHALL NOT require a `Chart.lock` for a chart that declares no
`dependencies:`, SHALL NOT run helm at all when no tracked chart declares
dependencies, and SHALL NOT consider untracked charts.

#### Scenario: No tracked chart declares dependencies
- **WHEN** no git-tracked `Chart.yaml` has a `dependencies:` list
- **THEN** the check passes without invoking helm

### Requirement: Locks can be regenerated with one command
`task helm:update-locks` SHALL run `helm dependency update` in every chart
directory that declares dependencies, SHALL resolve third-party and
`file://` sibling dependencies alike, and SHALL remove the downloaded
`charts/` build output unless that directory existed before the run. A
failure in one chart SHALL NOT prevent the remaining charts from being
updated, and SHALL make the command exit non-zero.

#### Scenario: Updating every umbrella chart
- **WHEN** `task helm:update-locks` is run in a clean checkout
- **THEN** each dependency-declaring chart's `Chart.lock` is regenerated
  and no `charts/` directory is left behind

### Requirement: helm state stays inside the repo
The update operation SHALL default `HELM_CACHE_HOME`, `HELM_CONFIG_HOME`,
and `HELM_DATA_HOME` to directories under `.tools/helm/` unless the caller
has set them, and SHALL resolve helm from `.tools/bin` before `PATH`,
exiting with status 2 and a setup hint when it is on neither.

#### Scenario: helm is not installed
- **WHEN** helm is on neither `.tools/bin` nor `PATH`
- **THEN** the operation and the check exit with status 2 and tell the
  user to run `task setup`

### Requirement: The lock check is a standing check in the five-layer pipeline
The check SHALL be implemented as a script, a `helm:check-locks` Taskfile
task, a skill, a rule indexed in `AGENTS.md`, and an entry in
`scripts/checks/check_all.bash`'s parallel list, so `task check:all` and
the `Checks` workflow run it with no workflow change, and its script and
the update script SHALL each have a mocked bats test.

#### Scenario: check:all runs the lock check
- **WHEN** `task check:all` is run
- **THEN** `helm:check-locks` runs in parallel with every other check and
  appears in the summary
