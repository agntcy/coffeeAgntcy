#!/usr/bin/env bash
# Ensures every git-tracked pyproject.toml has a sibling uv.lock that is in
# sync with it: runs `uv lock --check` in each such directory, which
# re-resolves the project and fails if the result would differ from the
# committed lock (a dependency added, removed, or re-pinned in
# pyproject.toml without re-running `uv lock`). It never rewrites a lock.
#
# A pyproject.toml with no sibling uv.lock is itself a failure, since an
# unlocked project can't be reproduced in CI or in a Docker build. A
# pyproject.toml that doesn't belong to a uv project can opt out with a
# `# uv-lock-exempt: <reason>` comment anywhere in the file; the reason
# is required (same opt-out shape as check_pinned_references.bash's
# `# pin-exempt:`).
#
# Resolves uv via .tools/bin first, falling back to PATH (see setup.sh).
# Resolution needs network access to the package indexes.
#
# See .agents/rules/quality/uv-lock-sync.md.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT" || exit 2

if [[ -x "$REPO_ROOT/.tools/bin/uv" ]]; then
    UV="$REPO_ROOT/.tools/bin/uv"
elif command -v uv >/dev/null 2>&1; then
    UV="$(command -v uv)"
else
    echo "error: uv not found - run ./scripts/setup.sh (or 'task setup') first." >&2
    exit 2
fi

mapfile -t pyprojects < <(git ls-files -- "pyproject.toml" "**/pyproject.toml")

failed=0
checked=0

for pyproject in "${pyprojects[@]}"; do
    dir="$(dirname "$pyproject")"

    if grep -qE '^[[:space:]]*#[[:space:]]*uv-lock-exempt:' "$pyproject"; then
        if grep -qE '^[[:space:]]*#[[:space:]]*uv-lock-exempt:[[:space:]]*[^[:space:]]' "$pyproject"; then
            continue
        fi
        echo "$pyproject: 'uv-lock-exempt' comment must state a reason, e.g. '# uv-lock-exempt: <why this has no uv.lock>'"
        failed=1
        continue
    fi

    if [[ ! -f "$dir/uv.lock" ]]; then
        echo "$pyproject: no sibling uv.lock - run 'uv lock' in $dir and commit it"
        failed=1
        continue
    fi

    checked=$((checked + 1))
    if ! output="$(cd "$dir" && "$UV" lock --check 2>&1)"; then
        echo "$pyproject: uv.lock is out of sync with pyproject.toml - run 'uv lock' in $dir and commit the result"
        printf '    %s\n' "${output//$'\n'/$'\n    '}"
        failed=1
    fi
done

if [[ "$failed" -eq 0 ]]; then
    echo "OK: $checked uv.lock file(s) in sync with their pyproject.toml."
fi

exit "$failed"
