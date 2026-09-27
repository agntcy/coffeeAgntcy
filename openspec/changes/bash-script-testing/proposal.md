# Proposal

## Why

Every script under `scripts/` is trusted with real consequences - CI gating,
toolchain installs, dashes/lint/pin/permission enforcement - but none of
them has a single automated test. A regression only surfaces when the
script runs for real (in CI, or against a human's machine), by which point
it's already blocking someone. This repo already treats "a script nobody
knows to run, a CI check with no local equivalent" as the exact failure
mode `.agents/rules/meta/repo-operation-pipeline.md` exists to prevent for
*operations*; the same gap exists one level down, inside each operation's
own script. This proposal introduces the convention, the pinned test
framework, a shared mocking helper, and the check/task/skill/rule layers
for it - it does not retrofit tests onto the ~20 scripts that predate this
rule. That backfill is explicitly out of scope here and left for a
follow-up effort, per the user's own framing of this change.

## What Changes

- **Pin a bash test framework**: `bats-core`, installed straight from its
  own GitHub source tarball (like `actionlint`/`shellcheck`/`shfmt`/`task`
  already are) into its own `.tools/bats/` directory (like `node`, since
  its `install.sh` always creates a bin/+libexec/+lib/ tree, not a single
  relocatable binary) - deliberately not through npm/Node, since it's a
  pure bash tool with no actual Node dependency of its own. `task setup`
  bootstraps it alongside every other pinned tool, with zero global
  install.
- **A shared mocking helper** (`scripts/lib/testing.sh`) any `.bats` file
  can `load`, providing a `mock_command` function that stubs an external
  binary (e.g. `gh`, `uname`) via a temp directory prepended to `PATH` for
  the duration of one test, so a script's own logic can be exercised
  without depending on a real network call, a real GitHub token, or the
  test machine's actual OS/architecture.
- **A convention, not a retrofit**: going forward, a shared helper under
  `scripts/lib/*.sh` gets unit tests for its functions (loaded via
  `source`, not run as a subprocess - these files are already meant to be
  sourced, never executed directly, so this needs no change to how they're
  written), and an executable script anywhere under `scripts/` gets a
  mocked end-to-end test that runs it as a real subprocess (`bats`'s
  `run`) with any external command it shells out to stubbed, and fixture
  input in place of real repo/API state.
- **Two worked reference examples**, both against existing, unmodified
  scripts (no retrofit needed for either, for the reason above):
  - `scripts/lib/tests/platform.bats` - unit tests for
    `scripts/lib/platform.sh`'s `detect_os`/`detect_arch_*` functions
    across every OS/arch branch (including the unsupported-input error
    path), by mocking `uname`.
  - `scripts/ci-gate/tests/wait-for-sibling-runs.bats` - a mocked
    end-to-end test of `scripts/ci-gate/wait-for-sibling-runs.sh`,
    mocking `gh` to return canned Actions-API JSON and overriding its
    timing env vars to run in real seconds instead of real minutes.
- **A coverage audit, not a hard "every script must have tests today"
  gate**: a new check (mirroring `check_pipeline_exceptions.bash`'s own
  "hardcoded exception list, audited" shape) fails only when a script
  *outside* a hardcoded "not yet tested" list lacks a corresponding test
  file - so every script that predates this rule is explicitly, visibly
  grandfathered (the punch list for the deferred follow-up), while any
  *new* script from now on is caught immediately if it ships without
  tests.
- **Full five-layer pipeline**: `task tests:bash` (run the suite) and
  `task tests:coverage` (run the audit) added to `check_all.bash`'s
  parallel list; a `testing-bash-scripts` skill; a `bash-script-testing`
  rule indexed in `AGENTS.md`.

## Capabilities

### New Capabilities

- `bash-script-testing`: the requirement that bash scripts in this repo
  have unit and/or mocked end-to-end tests, the pinned framework and
  shared mocking helper that make that practical, and the coverage audit
  that enforces it going forward without retroactively failing on
  pre-existing scripts.

### Modified Capabilities

None yet - `repo-tooling`'s "every standing check" requirement already
generalized to "any further check added to `check_all.bash`'s parallel
list" during the tree-reorganization work, so it doesn't need a further
edit to remain accurate once `tests:bash`/`tests:coverage` join that list.

## Impact

- New pinned tool (`bats`) in `scripts/lib/versions.sh`, a new install
  block in `scripts/setup.sh`.
- New shared library `scripts/lib/testing.sh`.
- New test files under `scripts/lib/tests/` and `scripts/ci-gate/tests/`.
- New check script, two new Taskfile tasks, one new skill, one new rule,
  `AGENTS.md` index updates, `scripts/checks/check_all.bash` gains two more
  parallel checks.
- No existing script's behavior changes.
