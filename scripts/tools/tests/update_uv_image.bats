#!/usr/bin/env bats
# Mocked end-to-end test for update_uv_image.bash. The script edits the
# tree at REPO_ROOT (default: the repo that contains it). Each test
# points REPO_ROOT at a fixture and supplies UV_IMAGE_DIGEST so the
# registry is never contacted. curl is mocked to fail if it is called.

load '../../lib/testing.sh'

SCRIPT="$BATS_TEST_DIRNAME/../update_uv_image.bash"

setup() {
    mock_setup
    mock_command curl 'echo "curl should not run" >&2; exit 99'
    FIXTURE="$BATS_TEST_TMPDIR/repo"
    rm -rf "$FIXTURE"
    OLD_VERSION="1.2.3"
    NEW_VERSION="9.9.9"
    OLD_DIGEST="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    NEW_DIGEST="sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    build_fixture "$OLD_VERSION" "$OLD_DIGEST"
}

teardown() {
    mock_teardown
}

build_fixture() {
    local version="$1" digest="$2"
    mkdir -p "$FIXTURE/scripts/lib" "$FIXTURE/docker"
    printf 'UV_VERSION="%s"\n' "$NEW_VERSION" >"$FIXTURE/scripts/lib/versions.sh"
    printf '%s %s\n' "$version" "$digest" >"$FIXTURE/scripts/lib/uv-image.txt"
    printf 'FROM astral/uv:%s-python3.13-trixie-slim@%s AS base\n' "$version" "$digest" >"$FIXTURE/docker/Dockerfile.python-agent"
}

run_sync() {
    REPO_ROOT="$FIXTURE" UV_IMAGE_DIGEST="$NEW_DIGEST" run "$SCRIPT"
}

@test "rewrites the uv digest to UV_VERSION and the supplied digest, without calling curl" {
    run_sync
    [ "$status" -eq 0 ]
    [[ "$output" != *"curl should not run"* ]]
    grep -q "^${NEW_VERSION} ${NEW_DIGEST}$" "$FIXTURE/scripts/lib/uv-image.txt"
    grep -q "@${NEW_DIGEST}" "$FIXTURE/docker/Dockerfile.python-agent"
    grep -q "python3.13-trixie-slim" "$FIXTURE/docker/Dockerfile.python-agent"
}

@test "a second run leaves the fixture unchanged and still does not call curl" {
    run_sync
    [ "$status" -eq 0 ]
    local before after
    before="$(mktemp -d)"
    cp -R "$FIXTURE/." "$before/"
    REPO_ROOT="$FIXTURE" UV_IMAGE_DIGEST="$NEW_DIGEST" run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"already matches"* ]]
    after="$(mktemp -d)"
    cp -R "$FIXTURE/." "$after/"
    diff -ru "$before" "$after"
}
