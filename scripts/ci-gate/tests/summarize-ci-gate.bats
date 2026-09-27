#!/usr/bin/env bats
# Mocked end-to-end test for scripts/ci-gate/summarize-ci-gate.sh. No
# external command needs mocking here - jq is a real, already-assumed
# system dependency (see the rule's own note) - so this just supplies a
# fixture runs.json (matching the exact shape wait-for-sibling-runs.sh
# writes, per its own test in wait-for-sibling-runs.bats) plus the env vars
# the script reads, and asserts on stdout / $GITHUB_STEP_SUMMARY.

load '../../lib/testing.sh'

SCRIPT="$BATS_TEST_DIRNAME/../summarize-ci-gate.sh"

setup() {
    mock_setup
    cd "$BATS_TEST_TMPDIR" || exit 1
    export GITHUB_RUN_ID="100"
    unset GITHUB_STEP_SUMMARY
}

teardown() {
    mock_teardown
}

write_runs_json() {
    cat >"$BATS_TEST_TMPDIR/runs.json"
    export RUNS_FILE="$BATS_TEST_TMPDIR/runs.json"
}

@test "SETTLED=true with all-clean siblings -> overall pass, table lists each sibling" {
    write_runs_json <<'JSON'
[
  {"id":100,"workflow_id":1,"name":"CI Gate","status":"completed","conclusion":"success","html_url":"https://example.com/runs/100"},
  {"id":200,"workflow_id":2,"name":"Checks","status":"completed","conclusion":"success","html_url":"https://example.com/runs/200"},
  {"id":201,"workflow_id":4,"name":"Deploy","status":"completed","conclusion":"skipped","html_url":"https://example.com/runs/201"}
]
JSON
    export SETTLED="true"

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Checks"* ]]
    [[ "$output" == *"Deploy"* ]]
    [[ "$output" == *":white_check_mark: pass"* ]]
    [[ "$output" != *":x: fail"* ]]
}

@test "SETTLED=false -> overall fail regardless of sibling statuses" {
    write_runs_json <<'JSON'
[
  {"id":100,"workflow_id":1,"name":"CI Gate","status":"completed","conclusion":"success","html_url":"https://example.com/runs/100"},
  {"id":200,"workflow_id":2,"name":"Checks","status":"completed","conclusion":"success","html_url":"https://example.com/runs/200"}
]
JSON
    export SETTLED="false"

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"hit the overall"* ]]
}

@test "a startup_failure/cancelled/timed_out sibling still fails overall even when SETTLED=true" {
    write_runs_json <<'JSON'
[
  {"id":100,"workflow_id":1,"name":"CI Gate","status":"completed","conclusion":"success","html_url":"https://example.com/runs/100"},
  {"id":200,"workflow_id":2,"name":"Checks","status":"completed","conclusion":"success","html_url":"https://example.com/runs/200"},
  {"id":300,"workflow_id":3,"name":"Deploy","status":"completed","conclusion":"cancelled","html_url":"https://example.com/runs/300"}
]
JSON
    export SETTLED="true"

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Deploy"* ]]
    [[ "$output" == *":x: fail"* ]]
}

@test "a sibling still in a non-completed status is judged failing at the row level" {
    write_runs_json <<'JSON'
[
  {"id":100,"workflow_id":1,"name":"CI Gate","status":"completed","conclusion":"success","html_url":"https://example.com/runs/100"},
  {"id":200,"workflow_id":2,"name":"Checks","status":"in_progress","conclusion":null,"html_url":"https://example.com/runs/200"}
]
JSON
    export SETTLED="true"

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Checks"* ]]
    [[ "$output" == *":x: fail"* ]]
}

@test "a sibling sharing the caller's own workflow_id is excluded from the table and the decision" {
    write_runs_json <<'JSON'
[
  {"id":100,"workflow_id":1,"name":"CI Gate","status":"completed","conclusion":"success","html_url":"https://example.com/runs/100"},
  {"id":101,"workflow_id":1,"name":"CI Gate","status":"in_progress","conclusion":null,"html_url":"https://example.com/runs/101"},
  {"id":200,"workflow_id":2,"name":"Checks","status":"completed","conclusion":"success","html_url":"https://example.com/runs/200"}
]
JSON
    export SETTLED="true"

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Checks"* ]]
    [[ "$output" != *"[CI Gate]"* ]]
}

@test "no sibling workflow runs found -> pass with placeholder row" {
    write_runs_json <<'JSON'
[
  {"id":100,"workflow_id":1,"name":"CI Gate","status":"completed","conclusion":"success","html_url":"https://example.com/runs/100"}
]
JSON
    export SETTLED="true"

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"no sibling workflow runs found for this commit"* ]]
}

@test "writes the summary to \$GITHUB_STEP_SUMMARY when set" {
    write_runs_json <<'JSON'
[
  {"id":100,"workflow_id":1,"name":"CI Gate","status":"completed","conclusion":"success","html_url":"https://example.com/runs/100"},
  {"id":200,"workflow_id":2,"name":"Checks","status":"completed","conclusion":"success","html_url":"https://example.com/runs/200"}
]
JSON
    export SETTLED="true"
    export GITHUB_STEP_SUMMARY="$BATS_TEST_TMPDIR/step_summary.md"

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [ -f "$GITHUB_STEP_SUMMARY" ]
    grep -q "Checks" "$GITHUB_STEP_SUMMARY"
    grep -q "CI Gate summary" "$GITHUB_STEP_SUMMARY"
}

@test "falls back to stdout when \$GITHUB_STEP_SUMMARY is unset" {
    write_runs_json <<'JSON'
[
  {"id":100,"workflow_id":1,"name":"CI Gate","status":"completed","conclusion":"success","html_url":"https://example.com/runs/100"},
  {"id":200,"workflow_id":2,"name":"Checks","status":"completed","conclusion":"success","html_url":"https://example.com/runs/200"}
]
JSON
    export SETTLED="true"
    unset GITHUB_STEP_SUMMARY

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"CI Gate summary"* ]]
    [[ "$output" == *"Checks"* ]]
}
