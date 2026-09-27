#!/usr/bin/env bats
# Mocked end-to-end test for scripts/lint/lint_shell.bash. The script finds
# every *.sh/*.bash file repo-wide via `find .` from its computed REPO_ROOT,
# with no override - so this copies the script into a fixture tree under
# $BATS_TEST_TMPDIR (the fixture-copy trick: REPO_ROOT is derived from
# BASH_SOURCE, so running the copy makes REPO_ROOT the fixture root instead
# of the real repo) and populates that tree with a couple of small shell
# files. shellcheck and shfmt are both mocked to report canned pass/fail
# output based on which fixture file they're invoked against, since the
# point here is testing lint_shell.bash's own orchestration (file
# discovery, exit code aggregation, --fix dispatch, resolve_tool's
# .tools/bin-vs-PATH fallback) rather than re-testing those tools.

load '../../lib/testing.sh'

setup() {
    mock_setup

    FIXTURE_REPO="$BATS_TEST_TMPDIR/repo"
    mkdir -p "$FIXTURE_REPO/scripts/lint"
    cp "$BATS_TEST_DIRNAME/../lint_shell.bash" "$FIXTURE_REPO/scripts/lint/lint_shell.bash"
    chmod +x "$FIXTURE_REPO/scripts/lint/lint_shell.bash"
    SCRIPT="$FIXTURE_REPO/scripts/lint/lint_shell.bash"

    mkdir -p "$FIXTURE_REPO/src"
    {
        echo '#!/usr/bin/env bash'
        echo 'echo hi'
    } >"$FIXTURE_REPO/src/clean.sh"

    export MARKER_FILE="$BATS_TEST_TMPDIR/shfmt_argv"
}

teardown() {
    mock_teardown
}

@test "no findings from shellcheck or shfmt -> exit 0" {
    mock_command shellcheck 'exit 0'
    mock_command shfmt 'exit 0'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: every shell script passes shellcheck and shfmt"* ]]
}

@test "shellcheck reports a finding -> exit 1, output shown" {
    echo 'x=1' >"$FIXTURE_REPO/src/bad.sh"

    mock_command shellcheck '
        for f in "$@"; do
            case "$f" in
            *bad*) echo "$f:1:1: note: fake shellcheck finding [SC9999]" ;;
            esac
        done
        [[ "$*" == *bad* ]] && exit 1
        exit 0
    '
    mock_command shfmt 'exit 0'

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"fake shellcheck finding"* ]]
}

@test "shfmt diff mode reports drift -> exit 1" {
    echo 'x=1' >"$FIXTURE_REPO/src/drift.sh"

    mock_command shellcheck 'exit 0'
    mock_command shfmt '
        if [[ "$1" == "-d" ]]; then
            for f in "$@"; do
                case "$f" in
                *drift*)
                    echo "--- $f.orig"
                    echo "+++ $f"
                    exit 1
                    ;;
                esac
            done
        fi
        exit 0
    '

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"drift.sh"* ]]
}

@test "--fix invokes shfmt -w instead of -d" {
    mock_command shellcheck 'exit 0'
    mock_command shfmt '
        echo "$@" >"$MARKER_FILE"
        exit 0
    '

    run "$SCRIPT" --fix
    [ "$status" -eq 0 ]
    [ -f "$MARKER_FILE" ]
    read -r argv <"$MARKER_FILE"
    [[ "$argv" == "-w "* ]]
}

@test "resolve_tool prefers a local .tools/bin/shellcheck over PATH" {
    mkdir -p "$FIXTURE_REPO/.tools/bin"
    cat >"$FIXTURE_REPO/.tools/bin/shellcheck" <<'STUB'
#!/usr/bin/env bash
echo "local-tools-bin-shellcheck-invoked"
exit 0
STUB
    chmod +x "$FIXTURE_REPO/.tools/bin/shellcheck"

    mock_command shellcheck 'echo "PATH-shellcheck-invoked"; exit 0'
    mock_command shfmt 'exit 0'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"local-tools-bin-shellcheck-invoked"* ]]
    [[ "$output" != *"PATH-shellcheck-invoked"* ]]
}

@test "resolve_tool falls back to PATH when .tools/bin has no shellcheck" {
    mock_command shellcheck 'echo "PATH-shellcheck-invoked"; exit 0'
    mock_command shfmt 'exit 0'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"PATH-shellcheck-invoked"* ]]
}
