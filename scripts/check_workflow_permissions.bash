#!/usr/bin/env bash
# Enforces least-privilege GITHUB_TOKEN permissions on every GitHub Actions
# workflow file under .github/workflows/:
#
#   1. Never grant `write-all` (workflow- or job-level) - it hands every
#      scope write access instead of naming only the ones actually needed.
#   2. Never leave permissions undeclared - a workflow-level `permissions:`
#      key covers every job, but if it's absent, every job must declare its
#      own, so nothing silently falls back to the default token permissions
#      (which depend on repo/org settings this file can't see).
#
# This only checks the policy (scopes actually granted); it doesn't validate
# workflow schema/syntax - see .agents/rules/workflow-least-privilege.md.
#
# Usage: scripts/check_workflow_permissions.bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT" || exit 2

shopt -s nullglob
files=(.github/workflows/*.yaml .github/workflows/*.yml)
shopt -u nullglob

if [ ${#files[@]} -eq 0 ]; then
    echo "No workflow files found under .github/workflows/."
    exit 0
fi

failed=0

for f in "${files[@]}"; do
    [ -f "$f" ] || continue

    # `permissions: write-all` is the only place `write-all` is valid at all
    # (it's a shorthand for every scope, not a per-scope value) - flag it
    # wherever it appears, workflow- or job-level, quoted or not, with or
    # without a trailing comment.
    # `'"'"'` splices a literal single-quote into this single-quoted -E
    # pattern (close ' / emit "'" / reopen ') so the pattern still reads as
    # `"?'?write-all"?'?` - an optional quote of either kind around write-all.
    write_all_lines="$(grep -nE '^[[:space:]]*permissions:[[:space:]]*"?'"'"'?write-all"?'"'"'?[[:space:]]*(#.*)?$' "$f" || true)"
    if [ -n "$write_all_lines" ]; then
        echo "FAIL: $f grants write-all - name only the scope(s) actually needed instead:"
        echo "$write_all_lines"
        failed=1
    fi

    # A workflow-level `permissions:` key (column 0) covers every job below
    # it by default, so there's nothing more to check for this file.
    if grep -qE '^permissions:' "$f"; then
        continue
    fi

    # No workflow-level permissions: every job must scope its own, or it
    # falls back to whatever the default token permissions happen to be.
    missing_jobs=()
    in_jobs=0
    current_job=""
    job_has_perms=0
    while IFS= read -r line; do
        if [[ "$line" =~ ^jobs:[[:space:]]*$ ]]; then
            in_jobs=1
            continue
        fi
        [ "$in_jobs" -eq 1 ] || continue
        if [[ "$line" =~ ^[A-Za-z] ]]; then
            in_jobs=0
        elif [[ "$line" =~ ^\ \ [A-Za-z0-9_.-]+:[[:space:]]*$ ]]; then
            if [ -n "$current_job" ] && [ "$job_has_perms" -eq 0 ]; then
                missing_jobs+=("$current_job")
            fi
            current_job="$(sed -E 's/^[[:space:]]*([A-Za-z0-9_.-]+):.*/\1/' <<<"$line")"
            job_has_perms=0
        elif [[ "$line" =~ permissions: ]]; then
            job_has_perms=1
        fi
    done <"$f"
    if [ -n "$current_job" ] && [ "$job_has_perms" -eq 0 ]; then
        missing_jobs+=("$current_job")
    fi

    if [ ${#missing_jobs[@]} -gt 0 ]; then
        echo "FAIL: $f has no workflow-level permissions: block, and job(s) missing their own: ${missing_jobs[*]}"
        failed=1
    fi
done

if [ "$failed" -ne 0 ]; then
    echo
    echo "Add an explicit permissions: block scoped to only what's needed (never write-all) - see .agents/rules/workflow-least-privilege.md."
    exit 1
fi

echo "Every workflow file declares explicit, non-write-all permissions."
