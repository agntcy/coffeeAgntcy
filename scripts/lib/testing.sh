#!/usr/bin/env bash
# Shared bats test helper: mocks an external command by putting an
# executable stub ahead of it on PATH for the duration of one test.
#
# Usage, inside a .bats file:
#   load '../../lib/testing.sh'
#
#   (bats' own `load` looks for "<path>.bash" first, falling back to the
#   exact path only if that doesn't exist - so the ".sh" extension above
#   must be given explicitly to find this file, unlike every other
#   `scripts/lib/*.sh` this repo already has.)
#
#   setup() {
#       mock_setup
#   }
#   teardown() {
#       mock_teardown
#   }
#
#   @test "uses the mocked gh" {
#       mock_command gh 'echo "{\"workflow_runs\":[]}"'
#       run gh api some/endpoint
#       [ "$status" -eq 0 ]
#   }
#
# mock_command's second argument is a literal shell command body, run
# verbatim as the stub's own script - "$@" is available inside it the same
# way it would be inside any shell function, so a stub can branch on the
# arguments it was called with when a test needs that.

# Prepends a fresh, per-test directory to PATH so mock_command has
# somewhere to write stubs, and so PATH can be restored exactly in
# mock_teardown. Call from a test file's own setup().
mock_setup() {
    MOCK_BIN_DIR="$(mktemp -d)"
    MOCK_ORIGINAL_PATH="$PATH"
    PATH="$MOCK_BIN_DIR:$PATH"
}

# Removes the mock bin directory and restores PATH to what it was before
# mock_setup. Call from a test file's own teardown().
mock_teardown() {
    PATH="$MOCK_ORIGINAL_PATH"
    [[ -n "${MOCK_BIN_DIR:-}" ]] && rm -rf "$MOCK_BIN_DIR"
}

# Writes an executable stub named "$1" into the mock bin directory, whose
# body is "$2" (a literal shell command, run with "$@" bound to whatever
# arguments the real command would have received). Requires mock_setup to
# have run first in the same test.
mock_command() {
    local name="$1" body="$2"
    : "${MOCK_BIN_DIR:?mock_command requires mock_setup to run first}"
    cat >"$MOCK_BIN_DIR/$name" <<EOF
#!/usr/bin/env bash
$body
EOF
    chmod +x "$MOCK_BIN_DIR/$name"
}
