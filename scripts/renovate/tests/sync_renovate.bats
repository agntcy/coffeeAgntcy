#!/usr/bin/env bats
# Mocked end-to-end test for scripts/renovate/sync_renovate.bash. The
# script resolves renovate via resolve_tool (same .tools/bin-vs-PATH
# pattern as lint_workflows.bash) then execs it from its computed
# REPO_ROOT. Same fixture-copy trick as lint_workflows.bats: copy the
# script into a fixture tree under $BATS_TEST_TMPDIR so REPO_ROOT becomes
# the fixture root, and mock renovate so no real network or GitHub call
# can happen - the point is testing sync_renovate.bash's own
# orchestration, not re-testing renovate.

load '../../lib/testing.sh'

setup() {
    mock_setup

    FIXTURE_REPO="$BATS_TEST_TMPDIR/repo"
    mkdir -p "$FIXTURE_REPO/scripts/renovate"
    cp "$BATS_TEST_DIRNAME/../sync_renovate.bash" "$FIXTURE_REPO/scripts/renovate/sync_renovate.bash"
    chmod +x "$FIXTURE_REPO/scripts/renovate/sync_renovate.bash"
    SCRIPT="$FIXTURE_REPO/scripts/renovate/sync_renovate.bash"
}

teardown() {
    mock_teardown
}

@test "runs renovate from the repo root and propagates success" {
    mock_command renovate 'echo "cwd=$(pwd -P)"; exit 0'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"cwd=$(cd "$FIXTURE_REPO" && pwd -P)"* ]]
}

@test "renovate failure -> same exit code, output shown" {
    mock_command renovate 'echo "fake renovate failure"; exit 3'

    run "$SCRIPT"
    [ "$status" -eq 3 ]
    [[ "$output" == *"fake renovate failure"* ]]
}

@test "arguments are passed through to renovate unchanged" {
    mock_command renovate 'echo "args=$*"; exit 0'

    run "$SCRIPT" --dry-run=full "owner/repo"
    [ "$status" -eq 0 ]
    [[ "$output" == *"args=--dry-run=full owner/repo"* ]]
}

@test "environment variables reach renovate" {
    mock_command renovate 'echo "platform=$RENOVATE_PLATFORM"; exit 0'

    RENOVATE_PLATFORM=github run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"platform=github"* ]]
}

@test "resolve_tool prefers a local .tools/bin/renovate over PATH" {
    mkdir -p "$FIXTURE_REPO/.tools/bin"
    cat >"$FIXTURE_REPO/.tools/bin/renovate" <<'STUB'
#!/usr/bin/env bash
echo "local-tools-bin-renovate-invoked"
exit 0
STUB
    chmod +x "$FIXTURE_REPO/.tools/bin/renovate"

    mock_command renovate 'echo "PATH-renovate-invoked"; exit 0'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"local-tools-bin-renovate-invoked"* ]]
    [[ "$output" != *"PATH-renovate-invoked"* ]]
}

@test "resolve_tool falls back to PATH when .tools/bin has no renovate" {
    mock_command renovate 'echo "PATH-renovate-invoked"; exit 0'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"PATH-renovate-invoked"* ]]
}

@test "renovate missing from both .tools/bin and PATH -> exit 2 with setup hint" {
    # Replace PATH with just the dirs the script itself needs (bash, dirname,
    # etc. via /usr/bin:/bin) minus any real renovate.
    PATH="$MOCK_BIN_DIR:/usr/bin:/bin" run "$SCRIPT"
    [ "$status" -eq 2 ]
    [[ "$output" == *"renovate not found"* ]]
}
