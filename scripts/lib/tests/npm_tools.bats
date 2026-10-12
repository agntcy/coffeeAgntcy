#!/usr/bin/env bats
# Unit tests for scripts/lib/npm_tools.sh: the package.json generated for
# the npm-installed tools carries exactly the versions pinned in versions.sh.

load '../versions.sh'
load '../npm_tools.sh'

@test "write_npm_tools_package_json: pins openspec and renovate to the versions.sh values" {
    write_npm_tools_package_json "$BATS_TEST_TMPDIR"

    grep -qF "\"@fission-ai/openspec\": \"$OPENSPEC_VERSION\"" "$BATS_TEST_TMPDIR/package.json"
    grep -qF "\"renovate\": \"$RENOVATE_VERSION\"" "$BATS_TEST_TMPDIR/package.json"
}

@test "write_npm_tools_package_json: output is valid JSON" {
    write_npm_tools_package_json "$BATS_TEST_TMPDIR"

    run python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$BATS_TEST_TMPDIR/package.json"
    [ "$status" -eq 0 ]
}
