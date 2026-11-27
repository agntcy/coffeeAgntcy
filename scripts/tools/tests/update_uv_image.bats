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
    # The real Dockerfile takes the tag from ARG UV_VERSION.
    printf '%s\n' 'ARG UV_VERSION' "FROM astral/uv:\${UV_VERSION}-python3.13-trixie-slim@${digest} AS base" >"$FIXTURE/docker/Dockerfile.python-agent"
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

# A registry mock: the auth endpoint returns a token, the manifest endpoint
# prints $MOCK_HEADERS (printf %b, so \r\n works).
mock_registry() {
    mock_command curl '
case "$*" in
    *auth.docker.io*) echo "{\"token\":\"tok\"}" ;;
    *) printf "%b" "$MOCK_HEADERS" ;;
esac'
}

@test "records the digest of the last response when the registry redirects to an image index" {
    mock_registry
    export MOCK_HEADERS="HTTP/2 307\r\ncontent-type: text/html\r\ndocker-content-digest: ${OLD_DIGEST}\r\n\r\nHTTP/2 200\r\ncontent-type: application/vnd.docker.distribution.manifest.list.v2+json\r\ndocker-content-digest: ${NEW_DIGEST}\r\n"
    REPO_ROOT="$FIXTURE" run "$SCRIPT"
    [ "$status" -eq 0 ]
    grep -q "^${NEW_VERSION} ${NEW_DIGEST}$" "$FIXTURE/scripts/lib/uv-image.txt"
    grep -q "@${NEW_DIGEST}" "$FIXTURE/docker/Dockerfile.python-agent"
}

@test "refuses a single-platform manifest" {
    mock_registry
    export MOCK_HEADERS="HTTP/2 200\r\ncontent-type: application/vnd.oci.image.manifest.v1+json\r\ndocker-content-digest: ${NEW_DIGEST}\r\n"
    REPO_ROOT="$FIXTURE" run "$SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == *"expected a manifest list or OCI index"* ]]
    grep -q "^${OLD_VERSION} ${OLD_DIGEST}$" "$FIXTURE/scripts/lib/uv-image.txt"
}

@test "fails on a record line that is not '<version> sha256:<64-hex>'" {
    printf '%s\n' 'garbage' >"$FIXTURE/scripts/lib/uv-image.txt"
    run_sync
    [ "$status" -ne 0 ]
    [[ "$output" == *"has a line that is not '<version> sha256:<64-hex>'"* ]]
}

@test "fails on a record with two digest lines" {
    printf '%s %s\n%s %s\n' "$OLD_VERSION" "$OLD_DIGEST" "$OLD_VERSION" "$OLD_DIGEST" >"$FIXTURE/scripts/lib/uv-image.txt"
    run_sync
    [ "$status" -ne 0 ]
    [[ "$output" == *"must contain exactly one digest line"* ]]
}

@test "fails on a supplied digest that is not sha256:<64-hex>" {
    REPO_ROOT="$FIXTURE" UV_IMAGE_DIGEST="sha256:short" run "$SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == *"digest must look like sha256:<64-hex>"* ]]
}

@test "fails when the Dockerfile FROM astral/uv line has no pinned digest" {
    printf '%s\n' 'ARG UV_VERSION' 'FROM astral/uv:${UV_VERSION}-python3.13-trixie-slim AS base' >"$FIXTURE/docker/Dockerfile.python-agent"
    run_sync
    [ "$status" -ne 0 ]
    [[ "$output" == *"has no digest-pinned FROM astral/uv line"* ]]
}

@test "fails when the token response has no token" {
    mock_command curl 'echo "{}"'
    rm "$FIXTURE/scripts/lib/uv-image.txt"
    REPO_ROOT="$FIXTURE" run "$SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == *"Docker Hub token response had no token"* ]]
}

@test "reads a token written with spaces around the colon" {
    mock_command curl '
case "$*" in
    *auth.docker.io*) echo "{\"token\" : \"tok\"}" ;;
    *) case "$*" in *"Bearer tok"*) printf "%b" "$MOCK_HEADERS" ;; *) echo "wrong token" >&2; exit 22 ;; esac ;;
esac'
    export MOCK_HEADERS="HTTP/2 200\r\ncontent-type: application/vnd.oci.image.index.v1+json\r\ndocker-content-digest: ${NEW_DIGEST}\r\n"
    REPO_ROOT="$FIXTURE" run "$SCRIPT"
    [ "$status" -eq 0 ]
    grep -q "^${NEW_VERSION} ${NEW_DIGEST}$" "$FIXTURE/scripts/lib/uv-image.txt"
}

@test "keeps the mode of the Dockerfile it rewrites" {
    chmod 644 "$FIXTURE/docker/Dockerfile.python-agent"
    run_sync
    [ "$status" -eq 0 ]
    [ -n "$(find "$FIXTURE/docker/Dockerfile.python-agent" -perm 644)" ]
}

@test "leaves no temp files behind after a failure" {
    export TMPDIR="$BATS_TEST_TMPDIR/tmp"
    mkdir -p "$TMPDIR"
    printf '%s\n' 'ARG UV_VERSION' 'FROM astral/uv:${UV_VERSION}-python3.13-trixie-slim AS base' >"$FIXTURE/docker/Dockerfile.python-agent"
    run_sync
    [ "$status" -ne 0 ]
    [ -z "$(ls -A "$TMPDIR")" ]
}
