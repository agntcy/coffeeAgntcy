#!/usr/bin/env bats
# Mocked end-to-end test for update_sigstore_lock.bash: UV_BIN points at a
# fake uv that records its arguments and the input file it was given, and
# writes the requested output file.

load '../../lib/testing.sh'

SCRIPT="$BATS_TEST_DIRNAME/../update_sigstore_lock.bash"

setup() {
    mock_setup
    export LOCK_DIR="$BATS_TEST_TMPDIR/lock"
    # Fake `uv pip compile <in> ... -o <out>`: records the arguments and the
    # input it saw, and writes a requirements file to the -o path.
    mock_command uv '
echo "$*" >"'"$BATS_TEST_TMPDIR"'/uv.args"
[ "$1" = "--no-config" ] && shift
in="$3"
cp "$in" "'"$BATS_TEST_TMPDIR"'/seen-input.txt"
while [ $# -gt 0 ]; do
    [ "$1" = "-o" ] && out="$2"
    shift
done
echo "generated" >"$out"
'
}

teardown() {
    mock_teardown
}

@test "compiles a universal, hashed, age-gated requirements file for the pinned sigstore on the lowest supported Python, ignoring uv config, and writes it" {
    export UV_BIN="$MOCK_BIN_DIR/uv"

    run "$SCRIPT"
    [ "$status" -eq 0 ]

    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/versions.sh"
    [[ "$(cat "$BATS_TEST_TMPDIR/uv.args")" == "--no-config pip compile "* ]]
    [[ "$(cat "$BATS_TEST_TMPDIR/uv.args")" == *" --universal --generate-hashes --no-header --exclude-newer 14 days --python-version 3.10 -o "* ]]
    [ "$(cat "$BATS_TEST_TMPDIR/seen-input.txt")" = "sigstore==$SIGSTORE_VERSION" ]
    [ "$(cat "$LOCK_DIR/requirements.txt")" = "generated" ]
}

@test "fails and leaves the existing file untouched when uv fails" {
    export UV_BIN="$MOCK_BIN_DIR/uv"
    mkdir -p "$LOCK_DIR"
    echo previous >"$LOCK_DIR/requirements.txt"
    mock_command uv 'exit 3'

    run "$SCRIPT"
    [ "$status" -ne 0 ]
    [ "$(cat "$LOCK_DIR/requirements.txt")" = "previous" ]
}
