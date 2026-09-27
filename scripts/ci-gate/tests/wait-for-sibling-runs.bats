#!/usr/bin/env bats
# Mocked end-to-end test for scripts/ci-gate/wait-for-sibling-runs.sh: runs
# the real script as a subprocess with `gh` mocked to return canned
# Actions-API JSON, and every timing knob overridden to run in real
# seconds instead of real minutes - no live GitHub API call, no waiting.

load '../../lib/testing.sh'

SCRIPT="$BATS_TEST_DIRNAME/../wait-for-sibling-runs.sh"

setup() {
    mock_setup
    cd "$BATS_TEST_TMPDIR" || exit 1
    export GITHUB_REPOSITORY="acme/repo"
    export GITHUB_RUN_ID="100"
    export HEAD_SHA="abc123"
    export SETTLE_DELAY_SECONDS="0"
    export POLL_INTERVAL_SECONDS="0"
    export CONSECUTIVE_CLEAN_POLLS_REQUIRED="1"
    export OVERALL_TIMEOUT_SECONDS="0"
}

teardown() {
    mock_teardown
}

@test "settles immediately when every sibling run is already completed" {
    # Self (id=100, workflow_id=1) plus one sibling on a different
    # workflow_id that's already completed - zero pending, one clean poll
    # is enough (CONSECUTIVE_CLEAN_POLLS_REQUIRED=1).
    mock_command gh '
cat <<JSON
{"id":100,"workflow_id":1,"name":"CI Gate","status":"in_progress"}
{"id":200,"workflow_id":2,"name":"Checks","status":"completed"}
JSON
'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"settled=true"* ]]
    [ -f runs.json ]
    run jq 'length' runs.json
    [ "$output" = "2" ]
}

@test "does not settle while a sibling run is still pending, and times out" {
    # Self (id=100, workflow_id=1) plus a sibling on a different
    # workflow_id still in_progress - stays pending, and
    # OVERALL_TIMEOUT_SECONDS=0 means it gives up on the very first poll
    # instead of actually waiting.
    mock_command gh '
cat <<JSON
{"id":100,"workflow_id":1,"name":"CI Gate","status":"in_progress"}
{"id":300,"workflow_id":3,"name":"Deploy","status":"in_progress"}
JSON
'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"settled=false"* ]]
    [[ "$output" == *"Deploy"* ]]
}

@test "never waits on another run of CI Gate itself sharing the same workflow_id" {
    # Two CI Gate runs (same workflow_id=1) sharing a commit - the
    # classic non-squash-merge deadlock this script exists to avoid. The
    # other CI Gate run (id=101) must not count as a pending sibling even
    # though it's still in_progress.
    mock_command gh '
cat <<JSON
{"id":100,"workflow_id":1,"name":"CI Gate","status":"in_progress"}
{"id":101,"workflow_id":1,"name":"CI Gate","status":"in_progress"}
{"id":200,"workflow_id":2,"name":"Checks","status":"completed"}
JSON
'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"settled=true"* ]]
}
