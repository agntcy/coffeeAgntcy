#!/usr/bin/env bats
# Unit tests for scripts/lib/versions.sh: asserts every pinned *_VERSION
# variable it defines is set, non-empty, and looks like a real version
# string, so a future typo (missing quotes, empty value, stray text)
# fails loudly instead of silently breaking whatever installs against it.

load '../versions.sh'

@test "TASK_VERSION is set and looks like a version string" {
    [ -n "$TASK_VERSION" ]
    [[ "$TASK_VERSION" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

@test "ACTIONLINT_VERSION is set and looks like a version string" {
    [ -n "$ACTIONLINT_VERSION" ]
    [[ "$ACTIONLINT_VERSION" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

@test "SHELLCHECK_VERSION is set and looks like a version string" {
    [ -n "$SHELLCHECK_VERSION" ]
    [[ "$SHELLCHECK_VERSION" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

@test "SHFMT_VERSION is set and looks like a version string" {
    [ -n "$SHFMT_VERSION" ]
    [[ "$SHFMT_VERSION" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

@test "BATS_VERSION is set and looks like a version string" {
    [ -n "$BATS_VERSION" ]
    [[ "$BATS_VERSION" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

@test "NODE_VERSION is set and looks like a version string" {
    [ -n "$NODE_VERSION" ]
    [[ "$NODE_VERSION" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

@test "UV_VERSION is set and looks like a version string" {
    [ -n "$UV_VERSION" ]
    [[ "$UV_VERSION" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

@test "OPENSPEC_VERSION is set and looks like a version string" {
    [ -n "$OPENSPEC_VERSION" ]
    [[ "$OPENSPEC_VERSION" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

@test "RENOVATE_VERSION is set and looks like a version string" {
    [ -n "$RENOVATE_VERSION" ]
    [[ "$RENOVATE_VERSION" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

@test "committed npm lockfile was generated for the pinned openspec and renovate versions" {
    local lock="$BATS_TEST_DIRNAME/../npm-tools/package-lock.json"
    [ -s "$lock" ]
    # The lockfile's root entry records the dependencies it was generated
    # for; `npm ci` fails on a mismatch, this fails earlier and by name.
    grep -qF "\"@fission-ai/openspec\": \"$OPENSPEC_VERSION\"" "$lock"
    grep -qF "\"renovate\": \"$RENOVATE_VERSION\"" "$lock"
}
