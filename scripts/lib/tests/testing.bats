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

# --- isolate_git_env ---------------------------------------------------------
# Builds a hostile "developer global git config": a core.hooksPath whose
# pre-commit hook rejects the commit (and leaves a marker file if it ran),
# plus commit.gpgsign with a gpg.program that always fails.
make_hostile_git_config() {
    HOSTILE_DIR="$BATS_TEST_TMPDIR/hostile"
    mkdir -p "$HOSTILE_DIR/hooks"
    printf '#!/bin/sh\ntouch "%s/hook-ran"\nexit 1\n' "$HOSTILE_DIR" \
        >"$HOSTILE_DIR/hooks/pre-commit"
    chmod +x "$HOSTILE_DIR/hooks/pre-commit"
    printf '#!/bin/sh\nexit 1\n' >"$HOSTILE_DIR/bad-gpg"
    chmod +x "$HOSTILE_DIR/bad-gpg"
    cat >"$HOSTILE_DIR/gitconfig" <<CFG
[core]
    hooksPath = $HOSTILE_DIR/hooks
[commit]
    gpgsign = true
[gpg]
    program = $HOSTILE_DIR/bad-gpg
CFG
    export GIT_CONFIG_GLOBAL="$HOSTILE_DIR/gitconfig"
    # The sandbox may also have a system config; keep it out of the baseline.
    export GIT_CONFIG_NOSYSTEM=1
}

commit_in_fresh_repo() {
    local repo="$BATS_TEST_TMPDIR/repo"
    rm -rf "$repo"
    mkdir -p "$repo"
    git -C "$repo" init -q
    git -C "$repo" config user.email "t@example.com"
    git -C "$repo" config user.name "T"
    echo x >"$repo/f"
    git -C "$repo" add f
    run git -C "$repo" commit -q -m "chore: add f"
}

@test "baseline: a hostile global git config breaks a commit without isolate_git_env" {
    make_hostile_git_config

    commit_in_fresh_repo

    [ "$status" -ne 0 ]
    [ -f "$HOSTILE_DIR/hook-ran" ]
}

@test "isolate_git_env lets a commit succeed despite a hostile global git config" {
    make_hostile_git_config

    isolate_git_env
    commit_in_fresh_repo

    [ "$status" -eq 0 ]
    [ ! -e "$HOSTILE_DIR/hook-ran" ]
}

@test "isolate_git_env unsets variables that select the outer repository" {
    export GIT_DIR=/nonexistent GIT_WORK_TREE=/nonexistent
    export GIT_INDEX_FILE=/nonexistent GIT_PREFIX=sub/

    isolate_git_env

    [ -z "${GIT_DIR+set}" ]
    [ -z "${GIT_WORK_TREE+set}" ]
    [ -z "${GIT_INDEX_FILE+set}" ]
    [ -z "${GIT_PREFIX+set}" ]
}

@test "isolate_git_env only exports variables and is safe to call twice" {
    local cwd_before="$PWD" path_before="$PATH"

    isolate_git_env
    isolate_git_env

    [ "$GIT_CONFIG_GLOBAL" = /dev/null ]
    [ "$GIT_CONFIG_SYSTEM" = /dev/null ]
    [ "$GIT_CONFIG_NOSYSTEM" = 1 ]
    [ "$PWD" = "$cwd_before" ]
    [ "$PATH" = "$path_before" ]
}
