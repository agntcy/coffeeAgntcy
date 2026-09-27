#!/usr/bin/env bats
# Unit tests for scripts/env.sh: sources it and asserts PATH gains the
# three repo-local toolchain directories, resolved against the correct
# repo root - both via `git rev-parse --show-toplevel` and via its `pwd`
# fallback when git fails.
#
# env.sh is never loaded via bats' own `load` here, because that would
# run it once automatically before every test with no chance to control
# cwd or mock git first - instead each test sources it explicitly, after
# setting up its own conditions.

load '../lib/testing.sh'

ENV_SH="$BATS_TEST_DIRNAME/../env.sh"

setup() {
    mock_setup
    ORIGINAL_PATH="$PATH"
}

teardown() {
    PATH="$ORIGINAL_PATH"
    mock_teardown
}

@test "env.sh: adds this repo's toolchain directories to PATH, resolved via git" {
    local repo_root
    repo_root="$(git rev-parse --show-toplevel)"

    source "$ENV_SH"

    [[ "$PATH" == "$repo_root/.tools/bin:$repo_root/.tools/node/bin:$repo_root/.tools/bats/bin:"* ]]
}

@test "env.sh: falls back to pwd for the repo root when git fails" {
    mock_command git 'exit 1'
    local work_dir="$BATS_TEST_TMPDIR/fallback-root"
    mkdir -p "$work_dir"
    cd "$work_dir" || return 1

    source "$ENV_SH"

    [[ "$PATH" == "$work_dir/.tools/bin:$work_dir/.tools/node/bin:$work_dir/.tools/bats/bin:"* ]]
}

@test "env.sh: unsets its own helper function and variable after sourcing" {
    source "$ENV_SH"

    run type -t _coffeeagntcy_repo_root
    [ "$status" -ne 0 ]
    [ -z "${_repo_root:-}" ]
}
