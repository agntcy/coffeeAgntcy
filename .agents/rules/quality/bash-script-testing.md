---
name: bash-script-testing
description: >-
  Every new bash script anywhere in this repository needs tests: a
  shared helper under a lib/*.sh-style directory gets unit tests for its
  functions (loaded via source), and an executable script gets a mocked
  end-to-end test that runs it as a subprocess with any external command
  it depends on stubbed. Checked by `task tests:coverage`
  (scripts/checks/check_bash_test_coverage.bash), which also runs as
  part of `task check:all` in .github/workflows/checks.yaml. Does not
  retroactively require tests on scripts that predate this rule - see
  its own allow-list.
---

# Bash script testing

## Rule

Every new bash script added anywhere in this repository needs tests, using `bats`
(`bats-core`, the same framework already pinned in
`scripts/lib/versions.sh` and bootstrapped by `task setup`):

- A shared helper under `scripts/lib/*.sh` - always `source`d by another
  script, never executed directly - gets **unit tests**: a `.bats` file
  sources it and calls its functions directly, mocking any external
  command those functions call (`uname`, etc.) via
  `scripts/lib/testing.sh`'s `mock_command`.
- An executable script anywhere else in the repository gets a **mocked
  end-to-end test**: a `.bats` file runs it as a real subprocess (`run
  path/to/script.bash ...`), with every external command it shells out
  to (`gh`, `docker`, `git`, ...) mocked the same way, and fixture input
  in place of real repo or API state.

A script's test lives at `<its-own-directory>/tests/<name>.bats` -
`scripts/checks/check_dashes.bash`'s test is
`scripts/checks/tests/check_dashes.bats`, `scripts/lib/platform.sh`'s is
`scripts/lib/tests/platform.bats`.

This does **not** retroactively require tests on any script that existed
before this rule was introduced - `scripts/checks/check_bash_test_coverage.bash`
carries its own hardcoded allow-list for exactly that purpose (currently
empty: every script in the repository has a test, including
`coffeeAGNTCY/coffee_agents/lungo/scripts/push_oasf_records.sh`, tested
for its current shape even though it's also the subject of its own
separate, already-planned refactor), the same shape as
`repo-operation-pipeline.md`'s own "Known exceptions" list, and only
fails when a script *outside* that list lacks a test.

## Why

None of this repo's scripts had a single automated test before this rule:
a regression only surfaced when the script ran for real, by which point
it was already blocking someone - CI gating, a toolchain install, a
dashes/lint/pin/permission check. Two kinds of script need two different
test shapes because retrofitting either one is unnecessary: a
`scripts/lib/*.sh` file is already safely `source`-able (it's never
executed directly), so unit-testing its functions needs no code change;
an executable script is already a self-contained subprocess a Taskfile
task or CI job invokes as-is, so a mocked end-to-end test needs no code
change either. Neither requires a `main()`-guard refactor or any other
restructuring - which is exactly why this rule could be introduced
without opening a project to retrofit tests onto every pre-existing
script first.

## How to apply

- Writing a new `scripts/lib/*.sh` helper: write
  `scripts/lib/tests/<name>.bats` alongside it, sourcing it directly and
  testing each function's real behavior, including its error paths - not
  just its happy path.
- Writing a new executable script anywhere in the repository: write
  `<its-directory>/tests/<name>.bats`, running it with `run` and mocking
  every external command it depends on - a passing test that secretly
  hit a real network call or a real installed tool isn't a mocked
  end-to-end test, it's an accidental integration test that only works
  on some machines.
- `load '../../lib/testing.sh'` (adjust the `../` count to the test
  file's own depth) for `mock_setup`/`mock_command`/`mock_teardown` - see
  [`scripts/lib/testing.sh`](../../../scripts/lib/testing.sh)'s own
  header comment for the exact usage shape, and
  [`scripts/ci-gate/tests/wait-for-sibling-runs.bats`](../../../scripts/ci-gate/tests/wait-for-sibling-runs.bats)
  for a worked example mocking a real external command (`gh`).
- To run the whole suite: `task tests:bash` (wraps
  [scripts/checks/check_bash_tests.bash](../../../scripts/checks/check_bash_tests.bash),
  see [Taskfile.yaml](../../../Taskfile.yaml)). To audit that every
  non-grandfathered script has one: `task tests:coverage` (wraps
  [scripts/checks/check_bash_test_coverage.bash](../../../scripts/checks/check_bash_test_coverage.bash)).
  Both run as part of `task check:all` and the `Checks` workflow.
- If a script genuinely predates this rule and still has no test, it's
  already listed in `check_bash_test_coverage.bash`'s `NOT_YET_TESTED`
  array - that's expected, not a bug, until the deferred backfill reaches
  it. Promote a script out of that list in the same change that finally
  gives it a test.
- This rule doesn't require "thorough" by automation - a test file
  existing is checkable, whether it actually exercises every meaningful
  branch isn't. Judge that the same way any other review judgment call
  gets made - see `self-review-after-change`/`pre-finalize-checks`.
- See the `testing-bash-scripts` skill for the full workflow.
