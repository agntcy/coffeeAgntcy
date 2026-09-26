# Spec Delta

## Purpose

Defines the behavior of `ci-gate.yaml`, this repo's single required
status check: it validates every workflow file, waits for every sibling
workflow run triggered on the same commit to reach a terminal state, and
reports a combined pass/fail decision - all in one self-contained
workflow with no manual list of other workflows to keep in sync.

## ADDED Requirements

### Requirement: CI Gate triggers on every pull request and every push to main
`ci-gate.yaml` SHALL run on every pull request (regardless of target
branch), every push to `main`, every push of a tag, and manual
`workflow_dispatch`.

#### Scenario: A pull request is opened
- **WHEN** a pull request is opened or updated, against any branch
- **THEN** `ci-gate.yaml` runs

### Requirement: Validation never blocks the wait step
CI Gate SHALL validate every file under `.github/workflows/` (the same
check as `task workflows:lint`), and SHALL proceed to wait for sibling
runs regardless of whether validation passed or failed.

#### Scenario: Validation fails
- **WHEN** a workflow file under `.github/workflows/` fails validation
- **THEN** CI Gate still proceeds to wait for sibling runs, and the
  overall run still fails once summarized

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
Once validation has completed and the wait step has finished (settled or
timed out), CI Gate SHALL write a table listing the validation result and
every sibling run's name, status, conclusion, and link, then decide
overall pass/fail: a sibling run counts as passing only if it is
`completed` with conclusion `success` or `skipped`; anything else
(`failure`, `startup_failure`, `cancelled`, `timed_out`, `neutral`, or
still pending when the timeout was reached) counts as failing. The
summary step SHALL always run, regardless of whether validation or the
wait step failed.

#### Scenario: Every sibling run succeeded and validation passed
- **WHEN** validation passed and every sibling run completed with
  `success` or `skipped`
- **THEN** the summary reports every check as passing and CI Gate exits
  zero

#### Scenario: A sibling run failed
- **WHEN** any sibling run completed with a conclusion other than
  `success` or `skipped`, or never reached `completed` before the
  timeout
- **THEN** the summary marks that run as failing and CI Gate exits
  non-zero, even if validation and every other sibling passed
