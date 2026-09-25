#!/usr/bin/env bash
# Lints and format-checks every shell script in the repo with shellcheck and
# shfmt (see .agents/rules/shell-script-linting.md and the shell:lint /
# shell:fmt tasks in Taskfile.yaml).
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

FIX=0
if [[ "${1:-}" == "--fix" ]]; then
    FIX=1
fi

SHFMT_OPTS=(-i 4 -ci)

mapfile -d '' -t files < <(find . \
    \( -path "*/node_modules" -o -path "*/.venv" -o -path "*/.git" \) -prune -o \
    -type f \( -name "*.sh" -o -name "*.bash" \) -print0)

if [[ ${#files[@]} -eq 0 ]]; then
    echo "No shell scripts found."
    exit 0
fi

echo "Checking ${#files[@]} shell script(s)..."

failed=0

if ! shellcheck "${files[@]}"; then
    failed=1
fi

if [[ "$FIX" -eq 1 ]]; then
    shfmt -w "${SHFMT_OPTS[@]}" "${files[@]}"
else
    if ! shfmt -d "${SHFMT_OPTS[@]}" "${files[@]}"; then
        failed=1
    fi
fi

if [[ "$failed" -eq 0 ]]; then
    echo "OK: every shell script passes shellcheck and shfmt"
fi

exit "$failed"
