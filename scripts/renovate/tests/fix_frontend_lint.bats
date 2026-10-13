#!/usr/bin/env bats
# Mocked end-to-end test for scripts/renovate/fix_frontend_lint.bash. The
# script is copied into a fixture tree under $BATS_TEST_TMPDIR so REPO_ROOT
# becomes the fixture root, and npm is mocked so nothing is installed.

load '../../lib/testing.sh'

setup() {
    mock_setup

    FIXTURE_REPO="$BATS_TEST_TMPDIR/repo"
    mkdir -p "$FIXTURE_REPO/scripts/renovate"
    cp "$BATS_TEST_DIRNAME/../fix_frontend_lint.bash" "$FIXTURE_REPO/scripts/renovate/fix_frontend_lint.bash"
    chmod +x "$FIXTURE_REPO/scripts/renovate/fix_frontend_lint.bash"
    SCRIPT="$FIXTURE_REPO/scripts/renovate/fix_frontend_lint.bash"

    for d in app/a/frontend app/b/frontend; do
        mkdir -p "$FIXTURE_REPO/$d"
        echo '{}' >"$FIXTURE_REPO/$d/package.json"
    done
    # Must be ignored: a package.json inside node_modules.
    mkdir -p "$FIXTURE_REPO/app/a/frontend/node_modules/x/frontend"
    echo '{}' >"$FIXTURE_REPO/app/a/frontend/node_modules/x/frontend/package.json"
}

teardown() {
    mock_teardown
}

@test "runs npm ci then npm run lint in every frontend, skipping node_modules" {
    mock_command npm 'echo "npm $* in $(basename "$(dirname "$PWD")")/$(basename "$PWD")"; exit 0'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"npm ci --ignore-scripts --no-audit --no-fund in a/frontend"* ]]
    [[ "$output" == *"npm run lint in a/frontend"* ]]
    [[ "$output" == *"npm ci --ignore-scripts --no-audit --no-fund in b/frontend"* ]]
    [[ "$output" == *"npm run lint in b/frontend"* ]]
    [[ "$output" != *"node_modules"* ]]
}

@test "unfixable lint problems do not fail the script" {
    mock_command npm '[[ "$1" == "run" ]] && exit 1; exit 0'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"could not fix"* ]]
}

@test "npm ci failure fails the script" {
    mock_command npm '[[ "$1" == "ci" ]] && { echo "install broke"; exit 4; }; exit 0'

    run "$SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == *"install broke"* ]]
}

@test "no frontends -> succeeds without calling npm" {
    rm -rf "$FIXTURE_REPO/app"
    mock_command npm 'echo "npm-called"; exit 0'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" != *"npm-called"* ]]
}
