#!/usr/bin/env bash
# Ensures every git-tracked Helm chart that declares dependencies has a
# committed Chart.lock that is in sync with them: copies every tracked
# chart directory into a scratch tree, runs
# scripts/helm/update_chart_locks.bash there (`helm dependency update`),
# and compares each resulting Chart.lock with the committed one, ignoring
# the `generated:` timestamp. It never rewrites a committed lock.
#
# Re-running the real update, rather than inspecting Chart.yaml and
# Chart.lock by hand, is what makes this catch every kind of drift:
# a third-party dependency re-pinned without refreshing the lock, a
# `file://` sibling chart whose Chart.yaml version no longer matches the
# pin (the update fails to resolve it), and a missing lock. (`helm
# dependency list` was tried and rejected: it only compares Chart.yaml with
# an uncommitted charts/ directory, so it reports every dependency as
# missing whether or not the lock is stale.)
#
# Resolves helm via .tools/bin first, falling back to PATH (see setup.sh).
# Resolution needs network access to the chart repositories and registries.
#
# See .agents/rules/quality/helm-chart-lock-sync.md.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
UPDATER="$SCRIPT_DIR/../helm/update_chart_locks.bash"
cd "$REPO_ROOT" || exit 2

if [[ $# -gt 0 ]]; then
    echo "Usage: $0" >&2
    exit 2
fi

SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

# Charts that declare dependencies, and every tracked file of every chart
# directory (siblings are resolved relative to each other, so all of them
# have to be present in the scratch tree).
chart_dirs=()
dependent_dirs=()
while IFS= read -r chart_file; do
    chart_dir="$(dirname "$chart_file")"
    chart_dirs+=("$chart_dir")
    grep -qE '^dependencies:' "$chart_file" && dependent_dirs+=("$chart_dir")
done < <(git ls-files -- "Chart.yaml" "**/Chart.yaml")

if [[ "${#dependent_dirs[@]}" -eq 0 ]]; then
    echo "OK: no Helm chart declares dependencies."
    exit 0
fi

for chart_dir in "${chart_dirs[@]}"; do
    git ls-files -z -- "$chart_dir"
done | tar --null -cf - -T - | tar -xf - -C "$SCRATCH"

"$UPDATER" "$SCRATCH" >"$SCRATCH/update.log" 2>&1
update_status=$?
if [[ "$update_status" -ne 0 ]]; then
    echo "error: 'helm dependency update' failed, so the committed Chart.lock files cannot be verified:"
    printf '    %s\n' "$(tail -n 20 "$SCRATCH/update.log")"
    echo "A failure naming a file:// subchart usually means the version pinned in that chart's Chart.yaml no longer matches the sibling chart's own version."
    exit "$update_status"
fi

failed=0
checked=0

for chart_dir in "${dependent_dirs[@]}"; do
    committed="$chart_dir/Chart.lock"
    regenerated="$SCRATCH/$chart_dir/Chart.lock"

    if [[ ! -f "$committed" ]]; then
        echo "$chart_dir: no Chart.lock - run 'task helm:update-locks' and commit it"
        failed=1
        continue
    fi

    checked=$((checked + 1))
    if ! delta="$(diff <(grep -v '^generated:' "$committed") <(grep -v '^generated:' "$regenerated"))"; then
        echo "$chart_dir: Chart.lock is out of sync with Chart.yaml - run 'task helm:update-locks' and commit the result"
        printf '    %s\n' "${delta//$'\n'/$'\n    '}"
        failed=1
    fi
done

if [[ "$failed" -eq 0 ]]; then
    echo "OK: $checked Chart.lock file(s) in sync with their Chart.yaml."
fi

exit "$failed"
