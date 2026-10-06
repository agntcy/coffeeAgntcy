#!/usr/bin/env bats
# Mocked end-to-end test for check_bash_tests.bash: mocks `bats` itself
# to confirm the wrapper discovers every tests/ directory repo-wide and
# passes them all to a single `bats --recursive` invocation, and
# propagates its exit code - without actually running the real suite
# (which would be circular). Uses the fixture-copy trick (the script
# computes REPO_ROOT from its own real location) so the discovered
# tests/ directories are deterministic fixture ones, not this repo's own
# ever-growing set.

load '../../lib/testing.sh'

REAL_SCRIPT="$BATS_TEST_DIRNAME/../check_bash_tests.bash"

setup() {
    mock_setup
    FIXTURE_ROOT="$BATS_TEST_TMPDIR/repo"
    mkdir -p "$FIXTURE_ROOT/scripts/checks"
    cp "$REAL_SCRIPT" "$FIXTURE_ROOT/scripts/checks/check_bash_tests.bash"
    chmod +x "$FIXTURE_ROOT/scripts/checks/check_bash_tests.bash"
    SCRIPT="$FIXTURE_ROOT/scripts/checks/check_bash_tests.bash"
}

teardown() {
    mock_teardown
}

@test "discovers every tests/ directory repo-wide and passes them all to one bats invocation" {
    mkdir -p "$FIXTURE_ROOT/scripts/lib/tests" "$FIXTURE_ROOT/other-project/scripts/tests"
    mock_command bats 'echo "called with: $*"; exit 0'

    TOOLS_BIN_DIR="$BATS_TEST_TMPDIR/no-such-dir" run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"called with: --recursive"* ]]
    [[ "$output" == *"./scripts/lib/tests"* ]]
    [[ "$output" == *"./other-project/scripts/tests"* ]]
}

@test "excludes tests/ directories under vendored/tooling directories" {
    mkdir -p "$FIXTURE_ROOT/scripts/lib/tests" \
        "$FIXTURE_ROOT/node_modules/some-pkg/tests" \
        "$FIXTURE_ROOT/.tools/lib/node_modules/bats/tests" \
        "$FIXTURE_ROOT/.venv/lib/tests"
    mock_command bats 'echo "called with: $*"; exit 0'

    TOOLS_BIN_DIR="$BATS_TEST_TMPDIR/no-such-dir" run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"./scripts/lib/tests"* ]]
    [[ "$output" != *"node_modules"* ]]
    [[ "$output" != *".venv"* ]]
}

@test "reports no tests/ directories found and exits 0 when none exist" {
    mock_command bats 'echo "should not be called"; exit 1'

    TOOLS_BIN_DIR="$BATS_TEST_TMPDIR/no-such-dir" run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"no tests/ directories found"* ]]
}

@test "propagates a failing bats run's exit code" {
    mkdir -p "$FIXTURE_ROOT/scripts/lib/tests"
    mock_command bats 'echo "not ok 1 something failed"; exit 1'

    TOOLS_BIN_DIR="$BATS_TEST_TMPDIR/no-such-dir" run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"not ok 1 something failed"* ]]
}
