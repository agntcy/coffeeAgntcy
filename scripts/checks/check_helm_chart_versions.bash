#!/usr/bin/env bash
# Automates Step 0 of docs/RELEASE-OPS.md ("Verify the Helm chart
# version-bump rule was followed") across every Helm chart in the repo at
# once, instead of the manual per-chart snippet described there.
#
# The rule (see CONTRIBUTING.md and
# .agents/rules/quality/helm-chart-version-bump.md): any change to a Helm
# chart's contents must be accompanied by a version bump in that chart's
# own Chart.yaml. Helm charts aren't tagged in git - the Chart.yaml
# `version` field is the only thing that identifies a published chart, so
# unbumped content is invisible to anything downstream.
#
# For each Chart.yaml found in the repo, this compares (across that
# chart's entire history, not scoped to any release tag):
#   - BODY: the newest commit touching the chart's contents (including its
#     own Chart.yaml, since appVersion/dependencies/etc. there count too)
#   - BUMP: the newest commit that changed the chart's own top-level
#     `version:` line in that chart's Chart.yaml
# and flags the chart if BODY is not an ancestor of (or equal to) BUMP
# (i.e. the body changed after, or without, a version bump).
#
# Deliberately not scoped to "since the last release tag": that would only
# catch a missing bump that happened after the last release, leaving an
# unbumped change from further back permanently invisible if it was never
# caught at the time (e.g. because this check didn't exist yet). The
# actual invariant - the newest content change is covered by an
# at-least-as-new version bump - has nothing to do with tags, so this
# checks each chart's whole history instead.
#
# Takes no arguments - always checks every chart as of HEAD. An earlier
# draft kept an optional [<end-ref>] for auditing an older ref; dropped
# since nothing calls it that way and a knob nothing exercises is a knob
# nobody's tested. See design.md under
# openspec/changes/helm-chart-version-guard/ if that's ever needed.
#
# This only detects that a bump is missing - it doesn't judge whether the
# bump should be patch/minor/major. Every flagged chart needs a bump,
# however trivial the diff (this is a CI merge gate with no trivial-diff
# exception) - see the checking-helm-chart-version-bumps skill for picking
# the bump level.
#
# Doesn't follow a chart directory's renames (git log's own limitation),
# so a body change from before a rename can be under-reported - a known,
# stated limitation, not a silent gap. See the helm-chart-version-bump
# rule.
#
# Needs full git history (`fetch-depth: 0`), not a shallow clone, to walk
# each chart's entire history - see .github/workflows/checks.yaml's
# checkout step.
#
# Usage: scripts/checks/check_helm_chart_versions.bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

if [[ $# -gt 0 ]]; then
    echo "Usage: $0" >&2
    exit 2
fi

failed=0

while IFS= read -r -d '' chart_file; do
    chart_dir="$(dirname "$chart_file")"

    body="$(git log -1 --format=%H -- "$chart_dir")"

    if [[ -z "$body" ]]; then
        continue # not yet committed
    fi

    bump="$(git log -1 --format=%H -G'^version:' -- "$chart_file")"

    if [[ -n "$bump" ]] && git merge-base --is-ancestor "$body" "$bump"; then
        continue # bumped at or after the newest content change
    fi

    echo "error: ${chart_dir} changed but its version was never bumped since (or was bumped before) that change" >&2
    failed=1
done < <(find . -iname "Chart.yaml" -not -path "*/node_modules/*" -print0)

if [[ "$failed" -eq 0 ]]; then
    echo "OK: every Helm chart's version reflects its latest content change"
fi

exit "$failed"
