#!/usr/bin/env bats
# Mocked end-to-end test for push_oasf_records.sh's current shape (see
# .agents/rules/quality/bash-script-testing.md and the design.md note on
# why this script was initially grandfathered, then tested for its
# current state anyway rather than waiting on its own separate,
# already-planned refactor).
#
# Uses the fixture-copy trick: the script self-locates its OASF
# directories relative to its own file location
# (SCRIPT_DIR=dirname($0), LUNGO_DIR=dirname(SCRIPT_DIR)), so copying it
# into $BATS_TEST_TMPDIR/repo/scripts/push_oasf_records.sh and creating
# fixture OASF directories/JSON files at matching paths under
# $BATS_TEST_TMPDIR/repo/ makes it operate entirely inside the fixture,
# with zero changes to the script itself. `dirctl` (the one external
# command it depends on) is mocked per test via mock_command; `jq` is
# left real, as this repo's other tests already do for system utilities
# that aren't the thing under test.
#
# The "dirctl not installed" test needs dirctl genuinely absent, so it
# uses mock_isolate_path (see scripts/lib/testing.sh) rather than
# guessing system directories that happen not to contain it. Only
# `dirname` is needed before the script's dirctl check (its shebang is
# the absolute /bin/bash, and the rest up to that point is builtins).

load '../../../../../scripts/lib/testing.sh'

REAL_SCRIPT="$BATS_TEST_DIRNAME/../push_oasf_records.sh"

setup() {
    mock_setup
    FIXTURE_ROOT="$BATS_TEST_TMPDIR/repo"
    mkdir -p "$FIXTURE_ROOT/scripts"
    cp "$REAL_SCRIPT" "$FIXTURE_ROOT/scripts/push_oasf_records.sh"
    chmod +x "$FIXTURE_ROOT/scripts/push_oasf_records.sh"
    AUCTION_DIR="$FIXTURE_ROOT/agents/supervisors/auction/oasf/agents"
    LOGISTICS_DIR="$FIXTURE_ROOT/agents/supervisors/logistics/oasf/agents"
}

teardown() {
    mock_teardown
}

write_json_agent() {
    local dir="$1" filename="$2" agent_name="$3"
    mkdir -p "$dir"
    if [[ -n "$agent_name" ]]; then
        printf '{"name": "%s"}\n' "$agent_name" >"$dir/$filename"
    else
        printf '{}\n' >"$dir/$filename"
    fi
}

# A dirctl stub that's "installed" and answers --version, but every real
# subcommand just fails loudly - used by tests that only care about
# argument parsing / server-addr resolution and never reach the OASF
# processing loop (because neither fixture OASF directory exists).
mock_dirctl_installed_only() {
    mock_command dirctl '
case "$1" in
    --version) echo "dirctl version fake" ;;
    *) echo "mock dirctl: unexpected call: $*" >&2; exit 1 ;;
esac
'
}

@test "--server-addr requires a value" {
    run "$FIXTURE_ROOT/scripts/push_oasf_records.sh" --server-addr
    [ "$status" -eq 1 ]
    [[ "$output" == *"--server-addr requires a host:port value"* ]]
}

@test "--server-addr rejects a value that looks like another flag" {
    run "$FIXTURE_ROOT/scripts/push_oasf_records.sh" --server-addr --foo
    [ "$status" -eq 1 ]
    [[ "$output" == *"--server-addr requires a host:port value"* ]]
}

@test "rejects an unknown option" {
    run "$FIXTURE_ROOT/scripts/push_oasf_records.sh" --nonsense
    [ "$status" -eq 1 ]
    [[ "$output" == *"unknown option: --nonsense"* ]]
}

@test "resolves the server address from --server-addr over the environment and default" {
    mock_dirctl_installed_only
    DIRECTORY_CLIENT_SERVER_ADDRESS="env-host:1111" \
        run "$FIXTURE_ROOT/scripts/push_oasf_records.sh" --server-addr cli-host:2222
    [ "$status" -eq 0 ]
    [[ "$output" == *"Directory target: cli-host:2222 (source: script --server-addr)"* ]]
}

@test "resolves the server address from the environment when no CLI flag is given" {
    mock_dirctl_installed_only
    DIRECTORY_CLIENT_SERVER_ADDRESS="env-host:1111" \
        run "$FIXTURE_ROOT/scripts/push_oasf_records.sh"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Directory target: env-host:1111 (source: DIRECTORY_CLIENT_SERVER_ADDRESS)"* ]]
}

@test "resolves the default server address when neither a CLI flag nor the environment variable is given" {
    mock_dirctl_installed_only
    run "$FIXTURE_ROOT/scripts/push_oasf_records.sh"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Directory target: 127.0.0.1:8888 (source: default)"* ]]
}

@test "dirctl not installed: prints install instructions and exits 1" {
    mock_isolate_path dirname
    run "$FIXTURE_ROOT/scripts/push_oasf_records.sh"
    [ "$status" -eq 1 ]
    [[ "$output" == *"dirctl is not installed"* ]]
    [[ "$output" == *"brew install dirctl"* ]]
}

@test "an OASF directory that does not exist is skipped with a warning, and nothing fails" {
    mock_dirctl_installed_only
    # Neither AUCTION_DIR nor LOGISTICS_DIR is created for this test.
    run "$FIXTURE_ROOT/scripts/push_oasf_records.sh"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Warning: Directory not found"* ]]
    [[ "$output" == *"Total OASF records found:  0"* ]]
}

@test "an agent already in the directory is not pushed" {
    write_json_agent "$AUCTION_DIR" "auctioneer.json" "auctioneer-agent"
    mock_command dirctl '
case "$3" in
    search) echo "[{\"cid\":\"existing\"}]" ;;
    *) echo "mock dirctl: unexpected call: $*" >&2; exit 1 ;;
esac
'
    run "$FIXTURE_ROOT/scripts/push_oasf_records.sh"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Already exists in directory"* ]]
    [[ "$output" == *"Already in directory:        1"* ]]
    [[ "$output" == *"Successfully pushed:         0"* ]]
}

@test "an agent not found is pushed, pulled, and published successfully" {
    write_json_agent "$AUCTION_DIR" "auctioneer.json" "auctioneer-agent"
    mock_command dirctl '
case "$3" in
    search) echo "[]" ;;
    push) echo "cid-abc123" ;;
    pull) exit 0 ;;
    routing) exit 0 ;;
    *) echo "mock dirctl: unexpected call: $*" >&2; exit 1 ;;
esac
'
    run "$FIXTURE_ROOT/scripts/push_oasf_records.sh"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Not found in directory, pushing"* ]]
    [[ "$output" == *"Successfully pushed (CID: cid-abc123"* ]]
    [[ "$output" == *"Successfully pushed:         1"* ]]
    [[ "$output" == *"Failed:                      0"* ]]
}

@test "dirctl search failing is treated as not found and falls through to push" {
    write_json_agent "$AUCTION_DIR" "auctioneer.json" "auctioneer-agent"
    mock_command dirctl '
case "$3" in
    search) echo "search exploded" >&2; exit 7 ;;
    push) echo "cid-abc123" ;;
    pull) exit 0 ;;
    routing) exit 0 ;;
    *) echo "mock dirctl: unexpected call: $*" >&2; exit 1 ;;
esac
'
    run "$FIXTURE_ROOT/scripts/push_oasf_records.sh"
    [ "$status" -eq 0 ]
    [[ "$output" == *"dirctl search failed (exit 7), treating as not found"* ]]
    [[ "$output" == *"Successfully pushed:         1"* ]]
}

@test "a JSON file with no extractable agent name is skipped and counted as failed" {
    write_json_agent "$AUCTION_DIR" "nameless.json" ""
    mock_dirctl_installed_only
    run "$FIXTURE_ROOT/scripts/push_oasf_records.sh"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Skipping nameless.json: Could not extract agent name"* ]]
    [[ "$output" == *"Failed:                      1"* ]]
}

@test "a failed push is counted as failed and shows the error output" {
    write_json_agent "$AUCTION_DIR" "auctioneer.json" "auctioneer-agent"
    mock_command dirctl '
case "$3" in
    search) echo "[]" ;;
    push) echo "some push error message" >&2; exit 1 ;;
    *) echo "mock dirctl: unexpected call: $*" >&2; exit 1 ;;
esac
'
    run "$FIXTURE_ROOT/scripts/push_oasf_records.sh"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Failed to push"* ]]
    [[ "$output" == *"some push error message"* ]]
    [[ "$output" == *"Failed:                      1"* ]]
}

@test "a successful push followed by a failed pull is counted as failed" {
    write_json_agent "$AUCTION_DIR" "auctioneer.json" "auctioneer-agent"
    mock_command dirctl '
case "$3" in
    search) echo "[]" ;;
    push) echo "cid-abc123" ;;
    pull) exit 3 ;;
    *) echo "mock dirctl: unexpected call: $*" >&2; exit 1 ;;
esac
'
    run "$FIXTURE_ROOT/scripts/push_oasf_records.sh"
    [ "$status" -eq 1 ]
    [[ "$output" == *"pull failed after push (exit 3)"* ]]
    [[ "$output" == *"Failed:                      1"* ]]
}

@test "a successful push and pull followed by a failed routing publish is counted as failed" {
    write_json_agent "$AUCTION_DIR" "auctioneer.json" "auctioneer-agent"
    mock_command dirctl '
case "$3" in
    search) echo "[]" ;;
    push) echo "cid-abc123" ;;
    pull) exit 0 ;;
    routing) exit 5 ;;
    *) echo "mock dirctl: unexpected call: $*" >&2; exit 1 ;;
esac
'
    run "$FIXTURE_ROOT/scripts/push_oasf_records.sh"
    [ "$status" -eq 1 ]
    [[ "$output" == *"routing publish failed for CID"* ]]
    [[ "$output" == *"Failed:                      1"* ]]
}

@test "processes multiple JSON files across both OASF directories and reports an accurate summary" {
    write_json_agent "$AUCTION_DIR" "existing.json" "existing-agent"
    write_json_agent "$AUCTION_DIR" "new.json" "new-agent"
    write_json_agent "$LOGISTICS_DIR" "broken.json" ""
    mock_command dirctl '
case "$3" in
    search)
        case "$*" in
            *existing-agent*) echo "[{\"cid\":\"existing\"}]" ;;
            *) echo "[]" ;;
        esac
        ;;
    push) echo "cid-new123" ;;
    pull) exit 0 ;;
    routing) exit 0 ;;
    *) echo "mock dirctl: unexpected call: $*" >&2; exit 1 ;;
esac
'
    run "$FIXTURE_ROOT/scripts/push_oasf_records.sh"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Total OASF records found:  3"* ]]
    [[ "$output" == *"Already in directory:        1"* ]]
    [[ "$output" == *"Successfully pushed:         1"* ]]
    [[ "$output" == *"Failed:                      1"* ]]
}
