#!/usr/bin/env bash
# Runs every bats test anywhere in the repository (see
# .agents/rules/quality/bash-script-testing.md) and fails if any of them
# do. Discovers every tests/ directory repo-wide (the same set
# check_bash_test_coverage.bash's SCAN_DIR=. covers) rather than
# hardcoding scripts/, so a test added under any other subproject (e.g.
# coffeeAGNTCY/coffee_agents/lungo/scripts/tests/) is actually run here,
# not just required to exist by the coverage audit. Resolves bats from
# the repo-local toolchain first so this also works before `source
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

mapfile -t test_dirs < <(find . \
    \( -path "*/node_modules" -o -path "*/.venv" -o -path "*/.git" -o -path "*/.tools" \) -prune -o \
    -type d -name tests -print | sort)

if [[ ${#test_dirs[@]} -eq 0 ]]; then
    echo "no tests/ directories found"
    exit 0
fi

exec "$BATS_BIN" --recursive "${test_dirs[@]}"
