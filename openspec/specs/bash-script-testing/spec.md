# bash-script-testing Specification

## Purpose
Requires every bash script in this repo, no exceptions, to have unit
and/or mocked end-to-end tests, and provides the pinned framework and
shared mocking helper that make that practical.

## Requirements

### Requirement: bats is bootstrapped by the pinned toolchain
`task setup` (`scripts/setup.sh`) SHALL install `bats-core` from its own
GitHub source tarball into the repo-local toolchain, pinned in
`scripts/lib/versions.sh`, the same way every other pinned tool is
installed - no global install, no Node dependency, reinstalled on any pin
mismatch.

#### Scenario: A fresh clone runs task setup
- **WHEN** `task setup` is run on a machine with no `.tools/` directory
- **THEN** a `bats` binary matching the pinned version is available on
  `PATH` after `source scripts/env.sh`

### Requirement: A shared mocking helper is available to any test
`scripts/lib/testing.sh` SHALL provide a `mock_command` function that,
for the duration of one test, makes an executable stub take priority over
any real binary of the same name on `PATH`, without permanently altering
the caller's environment.

#### Scenario: A test mocks an external command
- **WHEN** a `.bats` file loads `scripts/lib/testing.sh` and calls
  `mock_command` for a command name, then runs code that invokes that
  command name
- **THEN** the stub runs instead of any real binary of that name, and
  `PATH` is restored to its prior state once the test ends

### Requirement: A shared library's functions are unit-testable
Any lib/*.sh-style shared helper file anywhere in the repository SHALL be safely `source`-able by a test
without triggering a side effect, since these files are already never
executed directly - only `source`d by another script.

#### Scenario: A library file is sourced for its functions alone
- **WHEN** a `.bats` file sources a lib/*.sh-style shared helper file and calls one
  of its functions directly, with no other script invoking it
- **THEN** only that function's own logic runs - no side effect from
  anywhere else in the file

### Requirement: An executable script gets a mocked end-to-end test
Any script anywhere in the repository that is invoked as its own process (via a
Taskfile task, `check_all.bash`, or a workflow file) SHALL be testable end
to end by running it as a subprocess with any external command it
depends on mocked via `mock_command`, and fixture input in place of real
repo or API state.

#### Scenario: A script's happy path is exercised without real external state
- **WHEN** a `.bats` file mocks every external command a script invokes,
  supplies fixture input, and runs the script as a subprocess
- **THEN** the script's own logic (parsing, branching, output, exit code)
  is exercised and asserted on, with no real network call, API token, or
  dependency on the host machine's own state

### Requirement: A coverage audit enforces tests for every bash script, with no exceptions
A check SHALL fail when any bash script anywhere in the repository lacks
a corresponding test file. There is no allow-list or exceptions
mechanism - every script needs a test, full stop.

#### Scenario: A script ships with no test
- **WHEN** a bash script exists anywhere in the repository with no
  corresponding test file
- **THEN** the audit fails, naming that script's path

#### Scenario: Every script has a test
- **WHEN** the coverage audit runs and every bash script in the
  repository has a corresponding test file
- **THEN** the audit passes

### Requirement: The coverage audit and test suite run as part of every standing check
`task tests:bash` (runs the test suite) and `task tests:coverage` (runs
the coverage audit) SHALL both run as part of `task check:all`, in
parallel with every other standing check, the same as any check added to
`scripts/checks/check_all.bash`'s parallel list.

#### Scenario: task check:all is run
- **WHEN** `task check:all` is run
- **THEN** its summary table includes a pass/fail line for `tests:bash`
  and for `tests:coverage`
