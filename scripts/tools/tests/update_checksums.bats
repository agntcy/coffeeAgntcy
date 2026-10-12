#!/usr/bin/env bats
# Mocked end-to-end test for update_checksums.bash: curl is mocked to
# serve the URL itself as content, so each expected hash can be computed
# independently here, and CHECKSUMS_FILE points at a fixture instead of
# the real scripts/lib/checksums.txt.

load '../../lib/testing.sh'

SCRIPT="$BATS_TEST_DIRNAME/../update_checksums.bash"

setup() {
    mock_setup
    mock_command curl 'printf "%s" "${*: -1}"'
    export CHECKSUMS_FILE="$BATS_TEST_TMPDIR/checksums.txt"
}

teardown() {
    mock_teardown
}

@test "writes one sorted '<sha256>  <url>' line per distinct asset URL" {
    run "$SCRIPT"
    [ "$status" -eq 0 ]

    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/versions.sh"
    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/assets.sh"
    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/fetch.sh"

    run grep -vcE '^[0-9a-f]{64}  https://[^ ]+$' "$CHECKSUMS_FILE"
    [ "$output" = "0" ]

    [ "$(awk '{print $2}' "$CHECKSUMS_FILE")" = "$(awk '{print $2}' "$CHECKSUMS_FILE" | LC_ALL=C sort)" ]
    [ "$(awk '{print $2}' "$CHECKSUMS_FILE" | sort -u | wc -l)" -eq "$(wc -l <"$CHECKSUMS_FILE")" ]

    local url expected
    url="$(asset_url task linux arm64)"
    printf '%s' "$url" >"$BATS_TEST_TMPDIR/expected"
    expected="$(sha256_of "$BATS_TEST_TMPDIR/expected")"
    grep -qxF "$expected  $url" "$CHECKSUMS_FILE"
}
