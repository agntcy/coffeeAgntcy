#!/usr/bin/env bash
# Regenerates Chart.lock for every Helm chart that declares dependencies,
# by running `helm dependency update` in each such chart directory. This
# resolves third-party dependencies (OCI and https repositories) and
# `file://` sibling charts alike, which is what makes the result
# authoritative: it is the same operation Renovate runs when it bumps a
# chart dependency, and the one scripts/checks/check_helm_chart_locks.bash
# re-runs to detect a stale lock.
#
# The downloaded subcharts land in each chart's charts/ directory, which is
# build output and not committed, so it is removed again unless it already
# existed before the run. helm's cache, config, and data directories are
# kept under .tools/helm/ (unless the caller already set HELM_*_HOME) so
# nothing is written outside the repo.
#
# Resolves helm via .tools/bin first, falling back to PATH (see setup.sh).
# Needs network access to the chart repositories and registries.
#
# Usage: scripts/helm/update_chart_locks.bash [root-dir]
#   root-dir  tree to update instead of the repo root (the check script
#             points this at a scratch copy)
#
# See .agents/rules/quality/helm-chart-lock-sync.md.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ $# -gt 1 ]]; then
    echo "Usage: $0 [root-dir]" >&2
    exit 2
fi
ROOT="${1:-$REPO_ROOT}"

if [[ -x "$REPO_ROOT/.tools/bin/helm" ]]; then
    HELM="$REPO_ROOT/.tools/bin/helm"
elif command -v helm >/dev/null 2>&1; then
    HELM="$(command -v helm)"
else
    echo "error: helm not found - run ./scripts/setup.sh (or 'task setup') first." >&2
    exit 2
fi

export HELM_CACHE_HOME="${HELM_CACHE_HOME:-$REPO_ROOT/.tools/helm/cache}"
export HELM_CONFIG_HOME="${HELM_CONFIG_HOME:-$REPO_ROOT/.tools/helm/config}"
export HELM_DATA_HOME="${HELM_DATA_HOME:-$REPO_ROOT/.tools/helm/data}"

failed=0
updated=0

while IFS= read -r -d '' chart_file; do
    grep -qE '^dependencies:' "$chart_file" || continue
    chart_dir="$(dirname "$chart_file")"

    had_charts_dir=0
    [[ -e "$chart_dir/charts" ]] && had_charts_dir=1

    if "$HELM" dependency update "$chart_dir"; then
        updated=$((updated + 1))
    else
        echo "error: helm dependency update failed in ${chart_dir}" >&2
        failed=1
    fi

    [[ "$had_charts_dir" -eq 0 ]] && rm -rf "$chart_dir/charts"
done < <(find "$ROOT" -iname "Chart.yaml" -not -path "*/node_modules/*" -not -path "*/.tools/*" -not -path "*/charts/*" -print0 | sort -z)

if [[ "$failed" -eq 0 ]]; then
    echo "OK: updated Chart.lock for $updated chart(s) with dependencies."
fi

exit "$failed"
