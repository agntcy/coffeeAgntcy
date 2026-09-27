#!/usr/bin/env bats
# Mocked end-to-end test for check_bash_tests.bash: mocks `bats` itself
# to confirm the wrapper calls it with the right arguments and
# propagates its exit code, without actually running the real suite
# (which would be circular).

load '../../lib/testing.sh'

SCRIPT="$BATS_TEST_DIRNAME/../check_bash_tests.bash"

setup() {
    mock_setup
}

teardown() {
    mock_teardown
}

@test "invokes bats --recursive against scripts/ and passes through a clean exit" {
    mock_command bats 'echo "called with: $*"; exit 0'

    TOOLS_BIN_DIR="$BATS_TEST_TMPDIR/no-such-dir" run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"called with: --recursive scripts/"* ]]
}

@test "propagates a failing bats run's exit code" {
    mock_command bats 'echo "not ok 1 something failed"; exit 1'

    TOOLS_BIN_DIR="$BATS_TEST_TMPDIR/no-such-dir" run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"not ok 1 something failed"* ]]
}
