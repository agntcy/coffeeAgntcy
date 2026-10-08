#!/usr/bin/env bats
# Mocked end-to-end test for check_uv_locks.bash: the script finds
# pyproject.toml files with `git ls-files`, computes its own REPO_ROOT
# from BASH_SOURCE, and prefers $REPO_ROOT/.tools/bin/uv, so the fixture
# is a real git repo holding a copy of the script plus a fake uv whose
# `lock --check` result each test controls via the UV_EXIT variable file.

load '../../lib/testing.sh'

FIXTURE_REPO="$BATS_TEST_TMPDIR/repo"

setup() {
    mkdir -p "$FIXTURE_REPO/scripts/checks" "$FIXTURE_REPO/.tools/bin"
    cp "$BATS_TEST_DIRNAME/../check_uv_locks.bash" "$FIXTURE_REPO/scripts/checks/check_uv_locks.bash"
    chmod +x "$FIXTURE_REPO/scripts/checks/check_uv_locks.bash"
    SCRIPT="$FIXTURE_REPO/scripts/checks/check_uv_locks.bash"

    # Fake uv: records the directory it ran in, exits with the code in
    # $FIXTURE_REPO/uv_exit (default 0) for `lock --check`.
    cat >"$FIXTURE_REPO/.tools/bin/uv" <<EOS
#!/usr/bin/env bash
echo "\$PWD \$*" >> "$BATS_TEST_TMPDIR/uv.log"
[ "\$*" = "lock --check" ] || exit 64
if [ -f "$FIXTURE_REPO/uv_exit" ]; then
    echo "error: The lockfile at uv.lock needs to be updated"
    exit "\$(cat "$FIXTURE_REPO/uv_exit")"
fi
exit 0
EOS
    chmod +x "$FIXTURE_REPO/.tools/bin/uv"

    git -C "$FIXTURE_REPO" init -q
    git -C "$FIXTURE_REPO" config user.email "test@example.com"
    git -C "$FIXTURE_REPO" config user.name "Test"
}

add_project() {
    local dir="$1"
    mkdir -p "$FIXTURE_REPO/$dir"
    printf '[project]\nname = "x"\n' >"$FIXTURE_REPO/$dir/pyproject.toml"
}

stage_all() {
    git -C "$FIXTURE_REPO" add -A
}

@test "passes and runs uv lock --check in each project directory" {
    add_project a
    add_project b/c
    printf 'version = 1\n' >"$FIXTURE_REPO/a/uv.lock"
    printf 'version = 1\n' >"$FIXTURE_REPO/b/c/uv.lock"
    stage_all

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: 2 uv.lock file(s) in sync"* ]]
    grep -q "$FIXTURE_REPO/a lock --check" "$BATS_TEST_TMPDIR/uv.log"
    grep -q "$FIXTURE_REPO/b/c lock --check" "$BATS_TEST_TMPDIR/uv.log"
}

@test "fails, naming the pyproject, when uv reports the lock out of sync" {
    add_project a
    printf 'version = 1\n' >"$FIXTURE_REPO/a/uv.lock"
    echo 1 >"$FIXTURE_REPO/uv_exit"
    stage_all

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"a/pyproject.toml: uv.lock is out of sync"* ]]
    [[ "$output" == *"needs to be updated"* ]]
}

@test "fails when a pyproject.toml has no sibling uv.lock" {
    add_project a
    stage_all

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"a/pyproject.toml: no sibling uv.lock"* ]]
    [ ! -f "$BATS_TEST_TMPDIR/uv.log" ]
}

@test "skips a pyproject.toml carrying a uv-lock-exempt comment with a reason" {
    add_project a
    printf '# uv-lock-exempt: tooling config only, not a uv project\n' >>"$FIXTURE_REPO/a/pyproject.toml"
    stage_all

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: 0 uv.lock file(s) in sync"* ]]
}

@test "fails when a uv-lock-exempt comment states no reason" {
    add_project a
    printf '# uv-lock-exempt:\n' >>"$FIXTURE_REPO/a/pyproject.toml"
    stage_all

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"'uv-lock-exempt' comment must state a reason"* ]]
}

@test "errors out when uv is available neither in .tools/bin nor on PATH" {
    mock_setup
    rm "$FIXTURE_REPO/.tools/bin/uv"
    add_project a
    printf 'version = 1\n' >"$FIXTURE_REPO/a/uv.lock"
    stage_all

    # Restrict PATH to the real essentials so a developer's own uv can't leak in.
    PATH="$MOCK_BIN_DIR:/usr/bin:/bin" run "$SCRIPT"
    mock_teardown
    [ "$status" -eq 2 ]
    [[ "$output" == *"uv not found"* ]]
}
