# helm-chart-version-guard Specification

## Purpose
Requires a Helm chart's `Chart.yaml` `version:` field to be bumped at or
after that chart's own last real content change, checked across the
chart's entire git history rather than scoped to any release tag.

## Requirements

### Requirement: A chart's version reflects its own latest content change, across its whole history
For each Helm chart found in the repository, the check SHALL compare,
across that chart's entire git history with no lower bound, the newest
commit touching the chart's contents (including its own `Chart.yaml` -
`appVersion`/`dependencies`/etc. count as content) against the newest
commit that changed the chart's own top-level `version:` line, and SHALL
flag the chart when the former is not covered by (is not an ancestor of,
or equal to) the latter.

#### Scenario: Chart content changed after its last version bump
- **WHEN** a chart's contents (or its own `Chart.yaml`) were modified by a
  commit newer than the newest commit that changed its `version:` line
- **THEN** the chart is flagged as needing a version bump

#### Scenario: Chart content changed then bumped
- **WHEN** a chart's contents were modified by a commit, and a later
  commit bumps its `version:` line
- **THEN** the chart is not flagged

#### Scenario: A violation from before the last release tag is still detected
- **WHEN** a chart's contents changed without an accompanying version
  bump at some commit older than the repository's most recent release
  tag, and no further chart change has happened since
- **THEN** the chart is still flagged, regardless of how long ago that
  release tag was cut or whether a release tag exists at all

### Requirement: A brand-new chart needs no prior comparison
A chart's very first commit, which both adds its contents and sets an
initial `version:` value in the same commit, SHALL NOT be flagged, since
its content-change commit and its version-setting commit are one and the
same.

#### Scenario: A chart is newly added
- **WHEN** a chart directory is added for the first time, with its
  `Chart.yaml`'s `version:` field set in that same commit
- **THEN** the chart is not flagged

### Requirement: The check requires no baseline reference or arguments
The check SHALL run with no arguments, evaluating every chart's history up
to the current `HEAD`. It SHALL NOT require a release tag, a base ref, or
any other baseline to be supplied or looked up.

#### Scenario: Invoked with no arguments
- **WHEN** `task helm:check-versions` (or the underlying script directly)
  is run with no arguments
- **THEN** it evaluates every chart in the repository as of `HEAD`,
  without looking up or requiring any git tag

### Requirement: The check runs as part of every standing check
The check SHALL run as part of `task check:all`, in parallel with every
other standing check, the same as any check added to
`scripts/checks/check_all.bash`'s parallel list.

#### Scenario: task check:all is run
- **WHEN** `task check:all` is run
- **THEN** its summary table includes a pass/fail line for
  `helm:check-versions`
