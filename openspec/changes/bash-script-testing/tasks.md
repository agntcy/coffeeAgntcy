# Tasks

## 1. Pin and bootstrap bats

- [x] 1.1 Add `BATS_VERSION` to `scripts/lib/versions.sh`
- [x] 1.2 Add an install block to `scripts/setup.sh` that fetches
      `bats-core`'s own GitHub source tarball and runs its `install.sh`
      into a new `.tools/bats/` directory (not npm/node), including the
      same installed-version-matches-pin skip check every other tool
      already has; add `.tools/bats/bin` to `scripts/env.sh`'s `PATH`
- [x] 1.3 Run `task setup` from a machine state with `.tools/` moved aside;
      confirm `bats --version` matches the pin afterward

## 2. Shared mocking helper

- [x] 2.1 Write `scripts/lib/testing.sh`'s `mock_command` (creates an
      executable stub in a per-test temp dir, prepends it to `PATH`,
      restores `PATH` on teardown)
- [x] 2.2 Write `scripts/lib/tests/testing.bats` - a self-test of
      `mock_command` itself (a mocked command is found before the real
      one; `PATH` is restored after the test)

## 3. Reference examples (no existing script modified)

- [x] 3.1 Write `scripts/lib/tests/platform.bats`: unit tests for
      `detect_os`/`detect_arch_gnu`/`detect_arch_shellcheck`/
      `detect_arch_node`, mocking `uname` across Darwin/Linux,
      x86_64/amd64/arm64/aarch64, and an unsupported value for each
- [x] 3.2 Write `scripts/ci-gate/tests/wait-for-sibling-runs.bats`: a
      mocked end-to-end test of `wait-for-sibling-runs.sh`, mocking `gh`
      to return canned Actions-API JSON, with `SETTLE_DELAY_SECONDS`/
      `POLL_INTERVAL_SECONDS`/`CONSECUTIVE_CLEAN_POLLS_REQUIRED` overridden
      to run in real seconds; cover both the immediately-settled case and
      the still-pending-sibling case

## 4. Coverage audit

- [x] 4.1 Write `scripts/checks/check_bash_test_coverage.bash`: for every
      `scripts/**/*.bash`/`scripts/**/*.sh` (excluding `scripts/**/tests/`
      itself), fail if it has no corresponding `tests/<name>.bats` file
      and its path isn't in a hardcoded allow-list; seed that allow-list
      with every script that exists before this change
- [x] 4.2 Verify it passes clean against the repo as it stands (every
      current script is allow-listed); verify it correctly fails by
      temporarily adding a fake untested script outside the allow-list,
      then reverting

## 5. Wire up the pipeline

- [x] 5.1 Add `tests:bash` and `tests:coverage` Taskfile tasks
- [x] 5.2 Add both to `scripts/checks/check_all.bash`'s parallel list
- [x] 5.3 Write `.agents/skills/quality-checks/testing-bash-scripts/SKILL.md`
- [x] 5.4 Write `.agents/rules/quality/bash-script-testing.md`, cross-linking
      the script/task/skill/CI layers; add a row to
      `.agents/rules/always-apply/pre-finalize-checks.md`
- [x] 5.5 Index the new skill and rule in `AGENTS.md`'s tables
      (alphabetized within their section)

## 6. Verification

- [x] 6.1 Run `task check:all`, `task tests:bash`, `task tests:coverage`,
      `task shell:lint`, and `task links:check`; confirm all pass clean
- [x] 6.2 Run `openspec validate "bash-script-testing" --strict`
