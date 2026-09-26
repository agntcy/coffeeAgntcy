#!/usr/bin/env bash
# Lints every GitHub Actions workflow file under .github/workflows/ with
# actionlint (see the workflows:lint task in Taskfile.yaml).
#
# Prefers the repo-local toolchain installed by scripts/setup.sh into
# .tools/bin/ (pinned version in scripts/lib/versions.sh), falling back to
# whatever's already on PATH so this still works without running setup.sh
# first.
#
# This is the exact command that runs as part of `task check:all` in
# checks.yaml, so running it locally/as an agent before opening a PR
# catches the same findings ahead of time.
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

ACTIONLINT_BIN="$(resolve_tool actionlint)"

"$ACTIONLINT_BIN" -color
