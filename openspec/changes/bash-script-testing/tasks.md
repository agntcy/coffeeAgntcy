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

## 7. Broaden scope to the whole repository and backfill every pre-existing script

- [x] 7.1 Broaden `check_bash_test_coverage.bash`'s `SCAN_DIR` default
      from `scripts` to `.` (the whole repo, excluding `.git`/`.tools`/
      `node_modules`/`.venv`); broaden the rule/skill/`CONTRIBUTING.md`
      wording from "under `scripts/`" to "anywhere in the repository"
- [x] 7.2 Add `coffeeAGNTCY/coffee_agents/lungo/scripts/push_oasf_records.sh`
      (the one script found outside `scripts/`) to `NOT_YET_TESTED`,
      documenting why it's deliberately still deferred (a separate,
      already-planned refactor on a stashed branch)
- [x] 7.3 Write a real test for every one of the ~16 pre-existing scripts
      under `scripts/`: `scripts/lib/{fetch,versions}.sh`, `scripts/env.sh`,
      `scripts/setup.sh`, `scripts/checks/{check_all,check_dashes,
      check_forbidden_strings,check_markdown_links,
      check_pinned_references,check_pipeline_exceptions,
      check_workflow_permissions,find_strings,fix_dashes}.bash`,
      `scripts/ci-gate/summarize-ci-gate.sh`,
      `scripts/lint/{lint_shell,lint_workflows}.bash` - promoting each out
      of `NOT_YET_TESTED` as its test landed, until only the one
      deliberately-deferred entry from 7.2 remained
- [x] 7.4 Confirm `task check:all` (all 9 checks, 135 bash tests) passes
      clean with the fully-populated suite
- [x] 7.5 On explicit request, test
      `coffeeAGNTCY/coffee_agents/lungo/scripts/push_oasf_records.sh` for
      its current shape too (16 tests: argument parsing, server-address
      resolution precedence, the dirctl-not-installed path, a missing
      OASF directory, already-exists vs. push/pull/publish paths and
      their individual failure modes, and a multi-file summary), emptying
      `NOT_YET_TESTED` entirely; harden
      `check_bash_test_coverage.bash`'s now-empty array for `set -u` under
      bash <4.4 (`"${arr[@]:-}"`, not a bare `"${arr[@]}"`)

## 8. Fix a real CI failure (Ubuntu runner, not caught locally on macOS)

- [x] 8.1 Root-cause `scripts/lib/tests/fetch.bats`'s 6 CI failures: its
      "curl/wget/sudo/apt-get/id absent" simulation restricted `PATH` to
      `$MOCK_BIN_DIR:/bin`, assuming those tools "never live in bare
      /bin" - true on macOS, false on Debian/Ubuntu's merged-usr layout
      (`/bin` is a symlink to `/usr/bin`), so the real tools stayed
      reachable on the GitHub-hosted runner
- [x] 8.2 Add `mock_isolate_path` to `scripts/lib/testing.sh`: symlinks
      (not copies - a `cp` of a macOS system binary elsewhere gets killed
      by code-signing enforcement on exec) each named tool from the
      original `PATH` into the mock bin directory, then restricts `PATH`
      to only that directory; update `fetch.bats`'s 6 affected tests to
      use it instead of the `/bin`-guessing technique
- [x] 8.3 Remove `mock_command`'s own hidden dependency on external `cat`
      (rewritten with `echo`, both bash builtins), since a test isolating
      `PATH` that tightly would otherwise need to keep `cat` reachable
      purely for `mock_command`'s own sake
- [x] 8.4 Confirm all 153 tests pass locally and `task check:all` passes;
      real CI confirmation pending the next push

## 9. Remove the allow-list mechanism entirely (on explicit request)

- [x] 9.1 Remove `NOT_YET_TESTED`, `NOT_YET_TESTED_EXTRA`, and
      `is_grandfathered` from `check_bash_test_coverage.bash` - the check
      is now unconditional, no exceptions mechanism at all
- [x] 9.2 Update its own test (`check_bash_test_coverage.bats`): drop the
      "explicitly grandfathered" case, keep "has a test" (passes) and
      "fails when it doesn't" (including "reports every failing script")
- [x] 9.3 Update every doc that described the allow-list as a live
      mechanism to describe it only as something the backfill used
      temporarily: the rule, the skill, `CONTRIBUTING.md`, `Taskfile.yaml`
- [x] 9.4 Confirm `task check:all` passes clean with the simplified check
