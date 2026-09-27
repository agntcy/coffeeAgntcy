---
name: testing-bash-scripts
description: >-
  Writes unit tests (for scripts/lib/*.sh helpers) or mocked end-to-end
  tests (for executable scripts) using bats, and runs task
  tests:bash/tests:coverage. Use whenever adding a new script under
  scripts/, or when asked to test, mock, or audit test coverage for one.
---

# Testing bash scripts

## What this skill does

Writes a `.bats` test for a new script under `scripts/`, using `bats`
(bootstrapped by `task setup`) and this repo's shared mocking helper
([scripts/lib/testing.sh](../../../../scripts/lib/testing.sh)), then runs
[`task tests:bash`](../../../../Taskfile.yaml) (the whole suite) and
[`task tests:coverage`](../../../../Taskfile.yaml) (the audit that a test
exists at all). Both run as part of `task check:all` in
[checks.yaml](../../../../.github/workflows/checks.yaml). See
[.agents/rules/quality/bash-script-testing.md](../../../rules/quality/bash-script-testing.md)
for the underlying rule.

## Workflow

```
- [ ] 1. Decide which shape applies: a shared helper under scripts/lib/*.sh
        gets unit tests (source it, call its functions directly); an
        executable script anywhere else gets a mocked end-to-end test
        (run it as a subprocess with `run`).
- [ ] 2. Create <the script's own directory>/tests/<name>.bats.
- [ ] 3. At the top: `load '<relative path>/lib/testing.sh'` for
        mock_setup/mock_command/mock_teardown, plus (unit tests only)
        `load '<relative path>/<the file being tested>.sh'`.
- [ ] 4. For each external command the code under test invokes (gh,
        docker, uname, git, ...), call `mock_command <name> '<stub body>'`
        in the test that needs it, instead of letting the real binary
        run.
- [ ] 5. Write one @test per meaningful behavior - the happy path, every
        real branch, and every error path - not just one smoke test.
- [ ] 6. Run: task tests:bash (or `bats path/to/the.bats` directly while
        iterating, for a faster loop).
- [ ] 7. Run: task tests:coverage - confirms the new script is no longer
        flagged as untested.
```

## Notes

- Unit vs. mocked end-to-end is decided by what kind of file it is, not
  by choice: `scripts/lib/*.sh` files are already always `source`d, never
  executed directly, so they're naturally unit-testable with zero code
  change; executable scripts are already invoked as their own subprocess
  by a Taskfile task or CI, so they're naturally end-to-end-testable with
  `run` and zero code change either. Neither needs a `main()` guard or
  any other restructuring first.
- `mock_command <name> '<body>'` writes an executable stub named `<name>`
  ahead of the real command on `PATH` for the rest of that one test - the
  body runs as a real shell script, with `$@`/`$1`/etc. bound to whatever
  arguments the real command would have received, so a stub can branch on
  its arguments when a test needs different responses for different
  calls.
- A passing end-to-end test that quietly depended on a real installed
  tool or a real network call isn't actually mocked - if a test would
  fail differently (or not run at all) on a machine without that tool
  installed or without network access, something wasn't mocked that
  should have been.
- See [scripts/lib/tests/platform.bats](../../../../scripts/lib/tests/platform.bats)
  for a worked unit-test example (mocking `uname` to exercise every
  OS/arch branch) and
  [scripts/ci-gate/tests/wait-for-sibling-runs.bats](../../../../scripts/ci-gate/tests/wait-for-sibling-runs.bats)
  for a worked mocked end-to-end example (mocking `gh`).
- If `task tests:coverage` flags a script that genuinely predates this
  rule, that's the deferred backfill's own punch list, not a bug - see
  `check_bash_test_coverage.bash`'s `NOT_YET_TESTED` array. Don't silently
  add a new script to that list just to make the audit pass; it's only
  for scripts that existed before the rule did.
