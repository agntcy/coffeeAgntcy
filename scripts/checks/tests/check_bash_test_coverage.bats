#!/usr/bin/env bats
# Mocked end-to-end test for check_bash_test_coverage.bash: points it at a
# throwaway fixture tree (via SCAN_DIR) instead of the real repo, so it
# can be exercised against both branches (tested, untested) without
# depending on this repo's own current script inventory.

SCRIPT="$BATS_TEST_DIRNAME/../check_bash_test_coverage.bash"

setup() {
    FIXTURE_DIR="$BATS_TEST_TMPDIR/scripts"
    mkdir -p "$FIXTURE_DIR/checks/tests"
}

@test "passes when a script has a matching test file" {
    touch "$FIXTURE_DIR/checks/has_test.bash"
    touch "$FIXTURE_DIR/checks/tests/has_test.bats"

    SCAN_DIR="$FIXTURE_DIR" run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK:"* ]]
}

@test "fails, naming the script, when a script has no test" {
    touch "$FIXTURE_DIR/checks/new_and_untested.bash"

    SCAN_DIR="$FIXTURE_DIR" run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"$FIXTURE_DIR/checks/new_and_untested.bash has no test"* ]]
}

@test "reports every failing script, not just the first" {
    touch "$FIXTURE_DIR/checks/first_untested.bash"
    touch "$FIXTURE_DIR/checks/second_untested.bash"

    SCAN_DIR="$FIXTURE_DIR" run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"first_untested.bash has no test"* ]]
    [[ "$output" == *"second_untested.bash has no test"* ]]
}
