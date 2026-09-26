#!/usr/bin/env bash
# Polls the GitHub Actions runs API until every sibling workflow run
# triggered on the same commit reaches a terminal state (or a timeout
# elapses), then writes the collected runs to ./runs.json and a
# 'settled=true|false' line to $GITHUB_OUTPUT (or stdout, if unset).
#
# Uses the runs API rather than the checks API, which silently omits
# startup_failure runs.
#
# Excludes every run of this same workflow (CI Gate itself), not just this
# run's own id: a merge to main can produce more than one CI Gate run for
# the identical commit SHA (e.g. a non-squash merge keeps the PR's head
# SHA, so the pull_request-triggered run and the push-triggered run share
# a HEAD_SHA). Each such run waits on the other's "CI Gate" run turning up
# in the sibling list, so filtering by run id alone deadlocks both runs
# until the overall timeout. Filtering by workflow id instead means CI
# Gate never waits on itself, no matter how many of its own runs share a
# commit.
#
# Reads GITHUB_REPOSITORY, GITHUB_RUN_ID (both set automatically inside a
# real Actions run), HEAD_SHA (set by the calling workflow step), and needs
# an authenticated `gh` (GH_TOKEN, also preinstalled on Actions runners).
# Timing knobs default so this is also runnable by hand with a real gh
# session, not only inside CI.
set -uo pipefail

: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY must be set (owner/repo)}"
: "${GITHUB_RUN_ID:?GITHUB_RUN_ID must be set (the id of this run)}"
: "${HEAD_SHA:?HEAD_SHA must be set (the commit to find sibling runs for)}"
: "${SETTLE_DELAY_SECONDS:=60}"
: "${POLL_INTERVAL_SECONDS:=60}"
: "${OVERALL_TIMEOUT_SECONDS:=6000}"
: "${CONSECUTIVE_CLEAN_POLLS_REQUIRED:=2}"

self_run_id="$GITHUB_RUN_ID"
start_time=$(date +%s)
clean_polls=0
settled=false
last_good_runs_json='[]'

echo "Waiting ${SETTLE_DELAY_SECONDS}s for sibling runs to be scheduled..."
sleep "$SETTLE_DELAY_SECONDS"

while true; do
    if fetched=$(gh api "repos/${GITHUB_REPOSITORY}/actions/runs?head_sha=${HEAD_SHA}&per_page=100" \
        --paginate --jq '.workflow_runs[]' | jq -s '.'); then
        last_good_runs_json="$fetched"

        # Resolve our own workflow_id from this same payload every poll (the
        # self run is always included, since head_sha covers the commit this
        # run itself was triggered on) so runs of this workflow are never
        # treated as siblings to wait for - see the header comment above.
        own_workflow_id=$(jq -r --argjson self "$self_run_id" '
          [.[] | select(.id == $self) | .workflow_id] | first // empty
        ' <<<"$last_good_runs_json")

        IFS=$'\t' read -r pending pending_names <<<"$(jq -r --argjson self "$self_run_id" --argjson ownwf "${own_workflow_id:-null}" '
          [.[] | select(.id != $self) | select($ownwf == null or .workflow_id != $ownwf) | select(.status != "completed")] as $p
          | [($p | length), ($p | map("\(.name) (\(.status))") | join("; "))] | @tsv
        ' <<<"$last_good_runs_json")"

        if [[ "$pending" -eq 0 ]]; then
            clean_polls=$((clean_polls + 1))
        else
            clean_polls=0
        fi

        if [[ "$pending" -gt 0 ]]; then
            echo "pending=$pending clean_polls=$clean_polls - waiting on: $pending_names"
        else
            echo "pending=$pending clean_polls=$clean_polls"
        fi

        if [[ "$clean_polls" -ge "$CONSECUTIVE_CLEAN_POLLS_REQUIRED" ]]; then
            settled=true
            break
        fi
    else
        echo "::warning::failed to list workflow runs from the GitHub API this poll; will retry"
        clean_polls=0
    fi

    elapsed=$(($(date +%s) - start_time))
    if [[ "$elapsed" -ge "$OVERALL_TIMEOUT_SECONDS" ]]; then
        settled=false
        break
    fi

    sleep "$POLL_INTERVAL_SECONDS"
done

echo "$last_good_runs_json" >runs.json
echo "settled=$settled" | tee -a "${GITHUB_OUTPUT:-/dev/stdout}"
