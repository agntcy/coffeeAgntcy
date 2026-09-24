#!/usr/bin/env bash
# Automates Step 0 of docs/RELEASE-OPS.md ("Verify the Helm chart
# version-bump rule was followed") across every Helm chart in the repo at
# once, instead of the manual per-chart snippet described there.
#
# The rule (see CONTRIBUTING.md and .agents/rules/helm-chart-version-bump.md):
# any change to a Helm chart's contents must be accompanied by a version
# bump in that chart's own Chart.yaml. Helm charts aren't tagged in git -
# the Chart.yaml `version` field is the only thing that identifies a
# published chart, so unbumped content is invisible to anything downstream.
#
# For each Chart.yaml found in the repo that also existed at <base-ref>,
# this compares (within <base-ref>..<end-ref>):
#   - BODY: the newest commit touching the chart's contents (including its
#     own Chart.yaml, since appVersion/dependencies/etc. there count too)
#   - BUMP: the newest commit that changed the chart's own top-level
#     `version:` line in that chart's Chart.yaml
# and flags the chart if BODY exists and is not an ancestor of BUMP (i.e.
# the body changed after, or without, a version bump).
#
# This only detects that a bump is missing - it doesn't judge whether the
# bump should be patch/minor/major. Every flagged chart needs a bump,
# however trivial the diff (this is a CI merge gate with no trivial-diff
# exception) - see the checking-helm-chart-version-bumps skill for picking
# the bump level.
#
# Usage: scripts/check_helm_chart_versions.bash <base-ref> [<end-ref>]
#   <base-ref>: the previous release tag (or any earlier ref) to compare from
#   <end-ref>:  ref to compare up to (default: HEAD)
# Example: scripts/check_helm_chart_versions.bash 0.3.0
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <base-ref> [<end-ref>]" >&2
  exit 2
fi

BASE_REF="$1"
END_REF="${2:-HEAD}"

for ref in "$BASE_REF" "$END_REF"; do
  if ! git rev-parse --verify --quiet "${ref}^{commit}" >/dev/null; then
    echo "error: '${ref}' is not a valid git ref" >&2
    exit 2
  fi
done

failed=0

while IFS= read -r -d '' chart_file; do
  chart_dir="$(dirname "$chart_file")"

  if ! git cat-file -e "${BASE_REF}:${chart_file}" 2>/dev/null; then
    continue # chart didn't exist at base ref - nothing to compare
  fi

  body="$(git log -1 --format=%H "${BASE_REF}..${END_REF}" -- "$chart_dir")"
  bump="$(git log -1 --format=%H "${BASE_REF}..${END_REF}" -G'^version:' -- "$chart_file")"

  if [[ -z "$body" ]]; then
    continue # chart's contents didn't change
  fi

  if [[ -n "$bump" ]] && git merge-base --is-ancestor "$body" "$bump"; then
    continue # bumped at or after the newest body change
  fi

  echo "error: ${chart_dir} changed since ${BASE_REF} but its version was not bumped (or was bumped before the change)" >&2
  failed=1
done < <(find . -iname "Chart.yaml" -not -path "*/node_modules/*" -print0)

if [[ "$failed" -eq 0 ]]; then
  echo "OK: every Helm chart changed between ${BASE_REF} and ${END_REF} had its version bumped"
fi

exit "$failed"
