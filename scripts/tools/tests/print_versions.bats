#!/usr/bin/env bats
# End-to-end test for print_versions.bash against fixture versions files,
# plus a check that every pin in the real versions.sh is listed.

SCRIPT="$BATS_TEST_DIRNAME/../print_versions.bash"

@test "prints one aligned 'tool version hash' row per pin, sorted, stripping a leading v, '-' without a pinned hash" {
    cat >"$BATS_TEST_TMPDIR/versions.sh" <<'FIXTURE'
ZED_VERSION="2.0.0"
ALPHA_VERSION="v1.2.3"
FIXTURE
    VERSIONS_FILE="$BATS_TEST_TMPDIR/versions.sh" run "$SCRIPT"
    [ "$status" -eq 0 ]
    [ "${lines[0]}" = "alpha  1.2.3  -" ]
    [ "${lines[1]}" = "zed    2.0.0  -" ]
    [ "${#lines[@]}" -eq 2 ]
}

@test "lists every tool pinned in the real versions.sh" {
    run "$SCRIPT"
    [ "$status" -eq 0 ]
    local expected
    expected="$(grep -c '^[A-Z_]*_VERSION=' "$BATS_TEST_DIRNAME/../../lib/versions.sh")"
    [ "${#lines[@]}" -eq "$expected" ]
    [[ "$output" == *"renovate"* ]]
}

@test "third column is this machine's pinned archive hash for downloaded tools and the lockfile integrity for npm tools" {
    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/versions.sh"
    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/assets.sh"
    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/platform.sh"

    local url expected
    url="$(asset_url task "$(detect_os)" "$(detect_arch_gnu)")"
    expected="$(awk -v u="$url" '$2 == u {print $1}' "$BATS_TEST_DIRNAME/../../lib/checksums.txt")"
    [ -n "$expected" ]

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"task"*"$TASK_VERSION"*"$expected"* || "$output" == *"task"*"${TASK_VERSION#v}"*"$expected"* ]]
    [[ "$output" == *"renovate"*"$RENOVATE_VERSION"*"sha512-"* ]]
    [[ "$output" != *" - "* ]]
}
