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
    # Built from bash builtins only (echo, not a heredoc piped through
    # external `cat`) so a test using mock_isolate_path to make some
    # other real command genuinely absent doesn't also have to keep
    # `cat` reachable just for mock_command's own sake.
    {
        echo "#!/usr/bin/env bash"
        echo "$body"
    } >"$MOCK_BIN_DIR/$name"
    chmod +x "$MOCK_BIN_DIR/$name"
}

# For a test that needs a real command to be genuinely absent (not just
# hopefully-shadowed by pointing PATH at a system directory guessed not to
# contain it) - symlinks each named tool, resolved via `command -v`
# against the original pre-mock_setup PATH, into the mock bin directory,
# then restricts PATH to *only* that directory. A symlink, not a copy:
# macOS's own system binaries are code-signed to their exact path, so a
# `cp` elsewhere gets killed (SIGKILL) on exec, while a symlink still
# resolves to - and passes signature verification against - the
# original file. Guessing a "safe" system directory instead (e.g. bare
# /bin) doesn't port across OSes either: Debian/Ubuntu's merged-usr
# layout makes /bin a symlink to /usr/bin, so a tool believed "never in
# /bin" on macOS (curl, wget, sudo, apt-get, id all live under /usr/bin
# or /opt/homebrew there) turns out to be reachable via /bin on Linux
# too. Call after mock_setup and before any mock_command calls the test
# also needs (harmless either order, since this only ever adds files to
# the same MOCK_BIN_DIR, never removes any).
mock_isolate_path() {
    local tool real_path
    : "${MOCK_BIN_DIR:?mock_isolate_path requires mock_setup to run first}"
    for tool in "$@"; do
        real_path="$(PATH="$MOCK_ORIGINAL_PATH" command -v "$tool")" || {
            echo "mock_isolate_path: '$tool' not found on the original PATH" >&2
            return 1
        }
        ln -s "$real_path" "$MOCK_BIN_DIR/$tool"
    done
    PATH="$MOCK_BIN_DIR"
}
