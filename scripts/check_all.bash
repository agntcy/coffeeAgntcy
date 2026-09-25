#!/usr/bin/env bash
# Runs every standing check in this repo - dash/hyphen check, shell script
# lint+format, workflow file lint, workflow permission scoping, and pinned
# external references - in parallel, always running all of them regardless
# of earlier failures, then fails if any did. Each check's output is
# captured to its own log file (so concurrent output never interleaves),
# printed in a fixed order, followed by a result table.
#
# This is what task check:all runs, and what the "Checks" CI workflow runs
# after a single tooling bootstrap, instead of each check re-bootstrapping
# on its own runner. See .agents/rules/repo-operation-pipeline.md.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

LOG_DIR="$(mktemp -d)"
trap 'rm -rf "$LOG_DIR"' EXIT

labels=()
pids=()

start_check() {
    local label="$1"
    shift
    labels+=("$label")
    (
        "$@" >"$LOG_DIR/$label.log" 2>&1
        echo $? >"$LOG_DIR/$label.exit"
    ) &
    pids+=("$!")
}

start_check "dashes:check" "$SCRIPT_DIR/check_dashes.bash"
start_check "shell:lint" "$SCRIPT_DIR/lint_shell.bash"
start_check "workflows:lint" "$SCRIPT_DIR/lint_workflows.bash"
start_check "workflows:check-permissions" "$SCRIPT_DIR/check_workflow_permissions.bash"
start_check "pins:check" "$SCRIPT_DIR/check_pinned_references.bash"

for pid in "${pids[@]}"; do
    wait "$pid" 2>/dev/null || true
done

failed=0
for label in "${labels[@]}"; do
    echo "=== $label ==="
    cat "$LOG_DIR/$label.log"
    echo
    exit_code="$(cat "$LOG_DIR/$label.exit" 2>/dev/null || echo 1)"
    [[ "$exit_code" == "0" ]] || failed=1
done

echo "=== Summary ==="
for label in "${labels[@]}"; do
    exit_code="$(cat "$LOG_DIR/$label.exit" 2>/dev/null || echo 1)"
    if [[ "$exit_code" == "0" ]]; then
        echo "PASS: $label"
    else
        echo "FAIL: $label (exit $exit_code)"
    fi
done

if [[ "$failed" -ne 0 ]]; then
    exit 1
fi
echo "All checks passed."
