#!/usr/bin/env bats
# Mocked end-to-end test for scripts/lint/lint_workflows.bash. The script
# resolves actionlint via resolve_tool (same .tools/bin-vs-PATH pattern as
# lint_shell.bash) then runs `actionlint -color` from its computed
# REPO_ROOT, relying on actionlint's own default of discovering
# .github/workflows/*.y*ml relative to cwd. This uses the same
# fixture-copy trick as lint_shell.bats: copy the script into a fixture
# tree under $BATS_TEST_TMPDIR so REPO_ROOT becomes the fixture root, then
# mock actionlint to scan the fixture's .github/workflows itself and report
# canned pass/fail - the point is testing lint_workflows.bash's own
# orchestration, not re-testing actionlint.

load '../../lib/testing.sh'

setup() {
    mock_setup

    FIXTURE_REPO="$BATS_TEST_TMPDIR/repo"
    mkdir -p "$FIXTURE_REPO/scripts/lint"
    cp "$BATS_TEST_DIRNAME/../lint_workflows.bash" "$FIXTURE_REPO/scripts/lint/lint_workflows.bash"
    chmod +x "$FIXTURE_REPO/scripts/lint/lint_workflows.bash"
    SCRIPT="$FIXTURE_REPO/scripts/lint/lint_workflows.bash"

    mkdir -p "$FIXTURE_REPO/.github/workflows"
    cat >"$FIXTURE_REPO/.github/workflows/ci.yaml" <<'YAML'
name: CI
on: push
jobs:
    build:
        runs-on: ubuntu-latest
        steps:
            - run: echo hi
YAML
}

teardown() {
    mock_teardown
}

@test "no findings -> exit 0" {
    mock_command actionlint '
        for f in .github/workflows/*.y*ml; do
            [[ -e "$f" ]] || continue
        done
        exit 0
    '

    run "$SCRIPT"
    [ "$status" -eq 0 ]
}

@test "findings present -> exit 1, output shown" {
    cat >"$FIXTURE_REPO/.github/workflows/bad.yaml" <<'YAML'
name: Bad
on: push
jobs:
    build:
        runs-on: ubuntu-latest
        steps:
            - run: echo "BAD_WORKFLOW_MARKER"
YAML

    mock_command actionlint '
        found=0
        for f in .github/workflows/*.y*ml; do
            [[ -e "$f" ]] || continue
            if grep -q "BAD_WORKFLOW_MARKER" "$f"; then
                echo "$f:1:1: fake actionlint finding"
                found=1
            fi
        done
        exit "$found"
    '

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"fake actionlint finding"* ]]
}

@test "resolve_tool prefers a local .tools/bin/actionlint over PATH" {
    mkdir -p "$FIXTURE_REPO/.tools/bin"
    cat >"$FIXTURE_REPO/.tools/bin/actionlint" <<'STUB'
#!/usr/bin/env bash
echo "local-tools-bin-actionlint-invoked"
exit 0
STUB
    chmod +x "$FIXTURE_REPO/.tools/bin/actionlint"

    mock_command actionlint 'echo "PATH-actionlint-invoked"; exit 0'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"local-tools-bin-actionlint-invoked"* ]]
    [[ "$output" != *"PATH-actionlint-invoked"* ]]
}

@test "resolve_tool falls back to PATH when .tools/bin has no actionlint" {
    mock_command actionlint 'echo "PATH-actionlint-invoked"; exit 0'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"PATH-actionlint-invoked"* ]]
}
