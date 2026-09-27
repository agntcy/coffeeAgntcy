#!/usr/bin/env bash
# Runs every bats test under scripts/ (see
# .agents/rules/quality/bash-script-testing.md) and fails if any of them
# do. Thin wrapper around `bats --recursive`, resolving bats from the
# repo-local toolchain first so this also works before `source
# scripts/env.sh` has been run, the same way lint_shell.bash/
# lint_workflows.bash already resolve shellcheck/shfmt/actionlint.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT" || exit 2

# Overridable so this script's own test can force the PATH-mocked `bats`
# to take priority over this machine's real .tools/bats/bin/bats, the
# same way SCAN_DIR does for check_bash_test_coverage.bash's own test.
: "${TOOLS_BIN_DIR:=$REPO_ROOT/.tools/bats/bin}"

resolve_tool() {
    local name="$1"
    local local_bin="$TOOLS_BIN_DIR/$1"
    if [[ -x "$local_bin" ]]; then
        echo "$local_bin"
        return 0
    fi
    if command -v "$name" >/dev/null 2>&1; then
        command -v "$name"
        return 0
    fi
    echo "error: $name not found. Run ./scripts/setup.sh and 'source scripts/env.sh' first." >&2
    return 2
}

BATS_BIN="$(resolve_tool bats)"

exec "$BATS_BIN" --recursive scripts/
