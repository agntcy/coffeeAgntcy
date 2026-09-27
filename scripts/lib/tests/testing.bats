#!/usr/bin/env bats
# Self-test for scripts/lib/testing.sh's mock_command/mock_setup/
# mock_teardown - the shared helper every other .bats file in this repo
# loads to mock an external command.

load '../testing.sh'

setup() {
    mock_setup
}

teardown() {
    mock_teardown
}

@test "mock_command makes a stub take priority over the real command" {
    mock_command uname 'echo "mocked-output"'

    run uname
    [ "$status" -eq 0 ]
    [ "$output" = "mocked-output" ]
}

@test "mock_command's stub receives the real command's arguments" {
    mock_command uname 'echo "args: $*"'

    run uname -s -m
    [ "$status" -eq 0 ]
    [ "$output" = "args: -s -m" ]
}

@test "mock_setup/mock_teardown restore PATH and remove the mock bin dir" {
    # setup() already called mock_setup once for this test; it recorded
    # the pre-mock PATH in MOCK_ORIGINAL_PATH before prepending MOCK_BIN_DIR.
    local pre_mock_path="$MOCK_ORIGINAL_PATH"
    local mock_dir="$MOCK_BIN_DIR"
    [ "$PATH" != "$pre_mock_path" ]

    mock_teardown

    [ "$PATH" = "$pre_mock_path" ]
    [ ! -d "$mock_dir" ]

    # Re-establish a mock dir so the outer teardown() (which still runs
    # after this test) has something valid to clean up.
    mock_setup
}
