#!/usr/bin/env bats
# Mocked end-to-end test for update_npm_lock.bash: NPM_BIN points at a fake
# npm that records its arguments and the package.json it was given.

load '../../lib/testing.sh'

SCRIPT="$BATS_TEST_DIRNAME/../update_npm_lock.bash"

setup() {
    mock_setup
    export LOCK_DIR="$BATS_TEST_TMPDIR/lock"
    # Fake `npm install --package-lock-only --prefix <dir>`: records the
    # arguments and the package.json it saw, and writes a lockfile.
    mock_command npm '
echo "$*" >"'"$BATS_TEST_TMPDIR"'/npm.args"
prefix="$PWD"
cp "$prefix/package.json" "'"$BATS_TEST_TMPDIR"'/seen-package.json"
echo "{\"generated\": true}" >"$prefix/package-lock.json"
'
}

teardown() {
    mock_teardown
}

@test "generates package.json from versions.sh, runs a lockfile-only ignore-scripts install, and writes the lock" {
    export NPM_BIN="$MOCK_BIN_DIR/npm"

    run "$SCRIPT"
    [ "$status" -eq 0 ]

    [[ "$(cat "$BATS_TEST_TMPDIR/npm.args")" == *"install --package-lock-only --ignore-scripts"* ]]
    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/versions.sh"
    grep -qF "\"renovate\": \"$RENOVATE_VERSION\"" "$BATS_TEST_TMPDIR/seen-package.json"
    [ "$(cat "$LOCK_DIR/package-lock.json")" = '{"generated": true}' ]
}
