# Spec Delta

## Purpose

Defines the behavior of `ci-gate.yaml`, this repo's single required
status check: a no-op collector that waits for every sibling workflow
run triggered on the same commit to reach a terminal state and reports a
combined pass/fail decision - all in one self-contained workflow with no
manual list of other workflows to keep in sync, and no check logic of
its own. The actual checks (including workflow-file validation) run in
`checks.yaml` (see the `repo-tooling` capability), whose triggers are
kept aligned with CI Gate's own so it is always among the sibling runs
CI Gate collects.

## ADDED Requirements

### Requirement: CI Gate triggers on every pull request and every push to main
`ci-gate.yaml` SHALL run on every pull request (regardless of target
branch), every push to `main`, every push of a tag, and manual
`workflow_dispatch`.

#### Scenario: A pull request is opened
- **WHEN** a pull request is opened or updated, against any branch
- **THEN** `ci-gate.yaml` runs

### Requirement: CI Gate runs no checks of its own
`ci-gate.yaml` SHALL NOT itself validate workflow files or run any other
check - it SHALL only wait for and report on sibling workflow runs.
Workflow-file validation (`task workflows:lint`) SHALL run exclusively
as part of `checks.yaml`'s `task check:all`.

#### Scenario: A workflow file has a validation finding
- **WHEN** a workflow file under `.github/workflows/` fails `task
  workflows:lint`
- **THEN** `checks.yaml`'s run fails, and CI Gate's summary reports that
  failure via its "sibling run failed" handling - not via any validation
  step CI Gate runs itself

### Requirement: checks.yaml's triggers are kept aligned with CI Gate's
`checks.yaml` SHALL trigger on the same event set as `ci-gate.yaml`:
every pull request (regardless of target branch), every push to `main`,
every push of a tag, and manual `workflow_dispatch` - not a narrower
subset. This is what makes CI Gate's "no checks of its own" design safe:
CI Gate can rely on `checks.yaml` always being among the sibling runs it
collects, on every commit CI Gate itself runs on.

#### Scenario: A pull request targets a non-main branch
- **WHEN** a pull request is opened against a branch other than `main`
- **THEN** both `ci-gate.yaml` and `checks.yaml` run on it, so
  workflow-file validation still happens even though CI Gate itself
  checks nothing

### Requirement: CI Gate has no toolchain dependency of its own
`ci-gate.yaml` SHALL invoke `scripts/ci-gate/wait-for-sibling-runs.sh`
and `scripts/ci-gate/summarize-ci-gate.sh` directly (not via `task`, and
without bootstrapping this repo's pinned toolchain first) - these
scripts need only `bash`, `jq`, and an authenticated `gh`, all already
present on a GitHub-hosted runner. `task ci-gate:wait`/`task
ci-gate:summarize` remain available as the same scripts' Taskfile
entry points for local/agent use, per
`.agents/rules/repo-operation-pipeline.md`; CI Gate itself just doesn't
need to go through `task` to reach them.

#### Scenario: CI Gate runs
- **WHEN** `ci-gate.yaml` runs
- **THEN** it does not run `./scripts/setup.sh` or install any pinned
  tool - only checkout, then the two scripts directly

### Requirement: CI Gate waits for every sibling run on the same commit to finish
CI Gate SHALL poll for every other workflow run triggered on the same
commit SHA (the pull request's head SHA for a `pull_request` event, or
the pushed SHA otherwise) until each has reached a terminal (`completed`)
status, or until an overall timeout elapses. It SHALL wait an initial
settle delay before the first poll (so runs that haven't been scheduled
yet are still counted), and SHALL require a configured number of
consecutive polls with nothing pending before considering the set
settled - not just one.

#### Scenario: A sibling run is still in progress
- **WHEN** another workflow run on the same commit is not yet
  `completed`
- **THEN** CI Gate keeps polling rather than reporting settled

#### Scenario: The overall timeout is reached
- **WHEN** the overall timeout elapses before every sibling run reaches a
  terminal status
- **THEN** CI Gate treats the run as not settled, and every
  still-pending sibling counts as a failure in the summary

### Requirement: CI Gate never waits on a run of itself
CI Gate SHALL exclude every workflow run belonging to the CI Gate
workflow itself from the set of sibling runs it waits for - not only
this specific run's own ID, but every run sharing CI Gate's
`workflow_id` on the same commit.

#### Scenario: Two CI Gate runs share the same commit
- **WHEN** a non-squash merge (or any other event) produces more than
  one CI Gate run for the same commit SHA
- **THEN** neither run waits on the other, and both can settle
  independently of each other's status

### Requirement: The summary reports every sibling run and the overall decision
Once the wait step has finished (settled or timed out), CI Gate SHALL
write a table listing every sibling run's name, status, conclusion, and
link, then decide overall pass/fail: a sibling run counts as passing
only if it is `completed` with conclusion `success` or `skipped`;
anything else (`failure`, `startup_failure`, `cancelled`, `timed_out`,
`neutral`, or still pending when the timeout was reached) counts as
failing. The summary step SHALL always run, regardless of whether the
wait step settled or timed out.

#### Scenario: Every sibling run succeeded
- **WHEN** every sibling run (including `checks.yaml`) completed with
  `success` or `skipped`
- **THEN** the summary reports every check as passing and CI Gate exits
  zero

#### Scenario: A sibling run failed
- **WHEN** any sibling run completed with a conclusion other than
  `success` or `skipped`, or never reached `completed` before the
  timeout
- **THEN** the summary marks that run as failing and CI Gate exits
  non-zero, even if every other sibling passed
