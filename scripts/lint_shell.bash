#!/usr/bin/env bash
# Lints and format-checks every shell script in the repo with shellcheck and
# shfmt (see .agents/rules/shell-script-linting.md and the shell:lint /
# shell:fmt tasks in Taskfile.yaml).
#
# Prefers the repo-local toolchain installed by scripts/setup.sh into
# .tools/bin/ (pinned versions in scripts/lib/versions.sh), falling back to
# whatever's already on PATH so this still works without running setup.sh
# first.
#
# shfmt style pinned for this repo: 4-space indent, switch-case bodies
# indented (-i 4 -ci). Matches the existing style of
# coffeeAGNTCY/coffee_agents/lungo/scripts/push_oasf_records.sh.
#
# Usage: scripts/lint_shell.bash [--fix]
#   --fix: rewrite files in place with shfmt instead of reporting diffs
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

resolve_tool() {
    local name="$1"
    local local_bin="$REPO_ROOT/.tools/bin/$1"
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

SHELLCHECK_BIN="$(resolve_tool shellcheck)"
SHFMT_BIN="$(resolve_tool shfmt)"

FIX=0
if [[ "${1:-}" == "--fix" ]]; then
    FIX=1
fi

SHFMT_OPTS=(-i 4 -ci)

mapfile -d '' -t files < <(find . \
    \( -path "*/node_modules" -o -path "*/.venv" -o -path "*/.git" -o -path "*/.tools" \) -prune -o \
    -type f \( -name "*.sh" -o -name "*.bash" \) -print0)

if [[ ${#files[@]} -eq 0 ]]; then
    echo "No shell scripts found."
    exit 0
fi

echo "Checking ${#files[@]} shell script(s)..."

failed=0

if ! "$SHELLCHECK_BIN" "${files[@]}"; then
    failed=1
fi

if [[ "$FIX" -eq 1 ]]; then
    "$SHFMT_BIN" -w "${SHFMT_OPTS[@]}" "${files[@]}"
else
    if ! "$SHFMT_BIN" -d "${SHFMT_OPTS[@]}" "${files[@]}"; then
        failed=1
    fi
fi

if [[ "$failed" -eq 0 ]]; then
    echo "OK: every shell script passes shellcheck and shfmt"
fi

exit "$failed"
