#!/usr/bin/env bash
# Combines wait-for-sibling-runs.sh's ./runs.json into a job-summary table,
# and decides overall pass/fail. CI Gate runs no check of its own (see
# .agents/rules/repo-operation-pipeline.md and the ci-gate spec capability)
# - this is purely a summary of sibling runs.
#
# Reads: SETTLED ("true"/"false", from wait-for-sibling-runs.sh's output),
# GITHUB_RUN_ID (set automatically inside a real Actions run), and
# RUNS_FILE (defaults to ./runs.json, written by wait-for-sibling-runs.sh
# in the same job). Writes to $GITHUB_STEP_SUMMARY if set, else stdout.
#
# Excludes every run of this same workflow (CI Gate itself), matching
# wait-for-sibling-runs.sh's own exclusion: that script no longer waits for
# a sibling CI Gate run on the same commit (waiting on it can never
# resolve, since that run is doing the exact same wait right back), so
# runs.json can still contain one that's not yet completed. Judging it
# here by "is it completed" the way every other sibling run is judged
# would fail this job on a run this script has no business waiting on.
set -uo pipefail

: "${SETTLED:?SETTLED must be set (true/false, from wait-for-sibling-runs.sh)}"
: "${GITHUB_RUN_ID:?GITHUB_RUN_ID must be set (the id of this run)}"
: "${RUNS_FILE:=runs.json}"
: "${OVERALL_TIMEOUT_SECONDS:=6000}"

SUMMARY_FILE="${GITHUB_STEP_SUMMARY:-$(mktemp)}"

self_run_id="$GITHUB_RUN_ID"
overall_pass=true

declare -a rows=("Check"$'\t'"Status"$'\t'"Conclusion"$'\t'"Result")

# Resolve our own workflow_id from runs.json (the self run is always
# included, since it shares the commit the wait step queried) so a sibling
# CI Gate run that's still in progress is never judged as a failing
# sibling here - see the header comment above.
own_workflow_id=$(jq -r --argjson self "$self_run_id" '
  [.[] | select(.id == $self) | .workflow_id] | first // empty
' "$RUNS_FILE")

run_count=$(jq --argjson self "$self_run_id" --argjson ownwf "${own_workflow_id:-null}" '
  [.[] | select(.id != $self) | select($ownwf == null or .workflow_id != $ownwf)] | length
' "$RUNS_FILE")

if [[ "$run_count" -eq 0 ]]; then
    rows+=("_(no sibling workflow runs found for this commit)_"$'\t'""$'\t'""$'\t'"")
else
    while IFS=$'\t' read -r name status conclusion url; do
        if [[ "$status" != "completed" ]]; then
            result_pass=false
        else
            case "$conclusion" in
                success | skipped) result_pass=true ;;
                *) result_pass=false ;;
            esac
        fi

        if [[ "$result_pass" == "true" ]]; then
            icon=":white_check_mark: pass"
        else
            icon=":x: fail"
            overall_pass=false
        fi

        rows+=("[$name]($url)"$'\t'"$status"$'\t'"$conclusion"$'\t'"$icon")
    done < <(jq -r --argjson self "$self_run_id" --argjson ownwf "${own_workflow_id:-null}" '
      .[] | select(.id != $self) | select($ownwf == null or .workflow_id != $ownwf) |
      [.name, .status, (.conclusion // "-"), .html_url] | @tsv
    ' "$RUNS_FILE")
fi

# Pad every column to its widest cell so the raw markdown source - as seen
# in plain-text logs, which don't render tables - lines up too, not just
# the rendered version in the job summary UI.
col1_width=0
col2_width=0
col3_width=0
col4_width=0
for row in "${rows[@]}"; do
    IFS=$'\t' read -r c1 c2 c3 c4 <<<"$row"
    ((${#c1} > col1_width)) && col1_width=${#c1}
    ((${#c2} > col2_width)) && col2_width=${#c2}
    ((${#c3} > col3_width)) && col3_width=${#c3}
    ((${#c4} > col4_width)) && col4_width=${#c4}
done

{
    echo "## CI Gate summary"
    echo

    header=true
    for row in "${rows[@]}"; do
        IFS=$'\t' read -r c1 c2 c3 c4 <<<"$row"
        printf '| %-*s | %-*s | %-*s | %-*s |\n' "$col1_width" "$c1" "$col2_width" "$c2" "$col3_width" "$c3" "$col4_width" "$c4"

        if $header; then
            printf '|%s|%s|%s|%s|\n' \
                "$(printf '%*s' $((col1_width + 2)) '' | tr ' ' '-')" \
                "$(printf '%*s' $((col2_width + 2)) '' | tr ' ' '-')" \
                "$(printf '%*s' $((col3_width + 2)) '' | tr ' ' '-')" \
                "$(printf '%*s' $((col4_width + 2)) '' | tr ' ' '-')"
            header=false
        fi
    done
} >>"$SUMMARY_FILE"

if [[ "$SETTLED" != "true" ]]; then
    {
        echo
        echo ":warning: hit the overall ${OVERALL_TIMEOUT_SECONDS}s wait timeout before every sibling run reached a terminal status - anything still pending above is treated as a failure."
    } >>"$SUMMARY_FILE"
    overall_pass=false
fi

# Always show the table: inside a real Actions run this also duplicates it
# into the step's own log (the job-summary tab otherwise being the only
# place it'd show up); outside one, the table went straight to a scratch
# temp file that nothing else would ever display.
cat "$SUMMARY_FILE"
[[ -z "${GITHUB_STEP_SUMMARY:-}" ]] && rm -f "$SUMMARY_FILE"

if [[ "$overall_pass" != "true" ]]; then
    exit 1
fi
