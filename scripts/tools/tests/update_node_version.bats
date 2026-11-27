#!/usr/bin/env bats
# Mocked end-to-end test for update_node_version.bash. The script edits
# the tree at REPO_ROOT (default: the repo that contains it). Each test
# points REPO_ROOT at a fixture and supplies NODE_IMAGE_DIGEST so the
# registry is never contacted. curl is mocked to fail if it is called.

load '../../lib/testing.sh'

SCRIPT="$BATS_TEST_DIRNAME/../update_node_version.bash"

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
    mkdir -p \
        "$FIXTURE/scripts/lib" \
        "$FIXTURE/docker" \
        "$FIXTURE/coffeeAGNTCY/coffee_agents/corto/exchange/frontend" \
        "$FIXTURE/coffeeAGNTCY/coffee_agents/lungo/frontend"
    printf 'NODE_VERSION="%s"\n' "$NEW_VERSION" >"$FIXTURE/scripts/lib/versions.sh"
    printf '%s %s\n' "$version" "$digest" >"$FIXTURE/scripts/lib/node-image.txt"
    # The real Dockerfile takes the tag from ARG NODE_VERSION.
    printf '%s\n' 'ARG NODE_VERSION' "FROM node:\${NODE_VERSION}-alpine@${digest}" >"$FIXTURE/docker/Dockerfile.ui"
    local dir
    for dir in \
        "$FIXTURE/coffeeAGNTCY/coffee_agents/corto/exchange/frontend" \
        "$FIXTURE/coffeeAGNTCY/coffee_agents/lungo/frontend"; do
        cat >"$dir/package.json" <<EOF
{
  "engines": {
    "node": ">=${version}",
    "npm": ">=11.20.0"
  }
}
EOF
        cat >"$dir/package-lock.json" <<EOF
{
  "packages": {
    "": {
      "engines": {
        "node": ">=${version}",
        "npm": ">=11.20.0"
      }
    },
    "node_modules/left-alone": {
      "engines": {
        "node": ">=${version}"
      }
    }
  }
}
EOF
        printf -- '- **Node.js** %s or higher with **npm** 11.20.0 or higher\n' "$version" >"$dir/README.md"
    done
    printf -- '- **Node.js** %s or higher with **npm** 11.20.0 or higher\n' "$version" >"$FIXTURE/TUTORIAL.md"
    printf -- '- **Node.js** %s or higher with **npm** 11.20.0 or higher\n' "$version" >"$FIXTURE/coffeeAGNTCY/coffee_agents/corto/README.md"
    printf -- '- **Node.js** %s or higher with **npm** 11.20.0 or higher\n' "$version" >"$FIXTURE/coffeeAGNTCY/coffee_agents/lungo/README.md"
}

run_sync() {
    REPO_ROOT="$FIXTURE" NODE_IMAGE_DIGEST="$NEW_DIGEST" run "$SCRIPT"
}

@test "rewrites consumers to NODE_VERSION and the supplied digest, without calling curl" {
    run_sync
    [ "$status" -eq 0 ]
    [[ "$output" != *"curl should not run"* ]]
    grep -q "^${NEW_VERSION} ${NEW_DIGEST}$" "$FIXTURE/scripts/lib/node-image.txt"
    grep -q "@${NEW_DIGEST}" "$FIXTURE/docker/Dockerfile.ui"
    grep -q ">=${NEW_VERSION}" "$FIXTURE/coffeeAGNTCY/coffee_agents/lungo/frontend/package.json"
    # The dependency copy in the lockfile is not the root floor.
    grep -q ">=${OLD_VERSION}" "$FIXTURE/coffeeAGNTCY/coffee_agents/lungo/frontend/package-lock.json"
    grep -q ">=${NEW_VERSION}" "$FIXTURE/coffeeAGNTCY/coffee_agents/lungo/frontend/package-lock.json"
    grep -q "(\`NODE_VERSION\` in \`scripts/lib/versions.sh\`)" "$FIXTURE/TUTORIAL.md"
    grep -q "\\*\\*Node.js\\*\\* ${NEW_VERSION}" "$FIXTURE/TUTORIAL.md"
    grep -q "11.20.0" "$FIXTURE/TUTORIAL.md"
}

@test "a second run leaves the fixture unchanged and still does not call curl" {
    run_sync
    [ "$status" -eq 0 ]
    local before after
    before="$(mktemp -d)"
    cp -R "$FIXTURE/." "$before/"
    REPO_ROOT="$FIXTURE" NODE_IMAGE_DIGEST="$NEW_DIGEST" run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"already match"* ]]
    after="$(mktemp -d)"
    cp -R "$FIXTURE/." "$after/"
    # Compare file contents. cp -R preserves the bytes the script wrote.
    diff -ru "$before" "$after"
}

@test "fails and leaves a dependency floor alone when the root entry has no engines floor" {
    local lock="$FIXTURE/coffeeAGNTCY/coffee_agents/lungo/frontend/package-lock.json"
    printf '%s\n' '{' '  "packages": {' '    "": {' '      "engines": { "node": "^1.0.0" }' '    },' '    "node_modules/left-alone": {' "      \"engines\": { \"node\": \">=${OLD_VERSION}\" }" '    }' '  }' '}' >"$lock"
    run_sync
    [ "$status" -ne 0 ]
    [[ "$output" == *"has no root engines.node floor to rewrite"* ]]
    grep -q ">=${OLD_VERSION}" "$lock"
    ! grep -q ">=${NEW_VERSION}" "$lock"
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
    export MOCK_HEADERS="HTTP/2 307\r\ncontent-type: text/html\r\ndocker-content-digest: ${OLD_DIGEST}\r\n\r\nHTTP/2 200\r\ncontent-type: application/vnd.oci.image.index.v1+json\r\ndocker-content-digest: ${NEW_DIGEST}\r\n"
    REPO_ROOT="$FIXTURE" run "$SCRIPT"
    [ "$status" -eq 0 ]
    grep -q "^${NEW_VERSION} ${NEW_DIGEST}$" "$FIXTURE/scripts/lib/node-image.txt"
}

@test "refuses a single-platform manifest" {
    mock_registry
    export MOCK_HEADERS="HTTP/2 200\r\ncontent-type: application/vnd.docker.distribution.manifest.v2+json\r\ndocker-content-digest: ${NEW_DIGEST}\r\n"
    REPO_ROOT="$FIXTURE" run "$SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == *"expected a manifest list or OCI index"* ]]
    grep -q "^${OLD_VERSION} ${OLD_DIGEST}$" "$FIXTURE/scripts/lib/node-image.txt"
}

@test "fails on a record line that is not '<version> sha256:<64-hex>'" {
    printf '%s\n' 'garbage' >"$FIXTURE/scripts/lib/node-image.txt"
    run_sync
    [ "$status" -ne 0 ]
    [[ "$output" == *"has a line that is not '<version> sha256:<64-hex>'"* ]]
}

@test "fails on a record with two digest lines" {
    printf '%s %s\n%s %s\n' "$OLD_VERSION" "$OLD_DIGEST" "$OLD_VERSION" "$OLD_DIGEST" >"$FIXTURE/scripts/lib/node-image.txt"
    run_sync
    [ "$status" -ne 0 ]
    [[ "$output" == *"must contain exactly one digest line"* ]]
}

@test "fails on a supplied digest that is not sha256:<64-hex>" {
    REPO_ROOT="$FIXTURE" NODE_IMAGE_DIGEST="sha256:short" run "$SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == *"digest must look like sha256:<64-hex>"* ]]
}

@test "fails and leaves a doc alone when it has no Node.js install sentence" {
    printf '%s\n' 'Node.js is used for the UI.' >"$FIXTURE/TUTORIAL.md"
    run_sync
    [ "$status" -ne 0 ]
    [[ "$output" == *"TUTORIAL.md has no Node.js install sentence"* ]]
    [ "$(cat "$FIXTURE/TUTORIAL.md")" = 'Node.js is used for the UI.' ]
}

@test "skips an earlier versionless Node.js line and rewrites the install sentence" {
    printf '%s\n' 'Node.js powers the UI.' "- **Node.js** ${OLD_VERSION} or higher with **npm** 11.20.0 or higher" >"$FIXTURE/TUTORIAL.md"
    run_sync
    [ "$status" -eq 0 ]
    [ "$(sed -n 1p "$FIXTURE/TUTORIAL.md")" = 'Node.js powers the UI.' ]
    sed -n 2p "$FIXTURE/TUTORIAL.md" | grep -q "\\*\\*Node.js\\*\\* ${NEW_VERSION} (\`NODE_VERSION\` in \`scripts/lib/versions.sh\`) or higher"
}

@test "fails when the Dockerfile FROM node line has no pinned digest" {
    printf '%s\n' 'ARG NODE_VERSION' 'FROM node:${NODE_VERSION}-alpine' >"$FIXTURE/docker/Dockerfile.ui"
    run_sync
    [ "$status" -ne 0 ]
    [[ "$output" == *"has no digest-pinned FROM node line"* ]]
}

@test "fails when the token response has no token" {
    mock_command curl 'echo "{}"'
    rm "$FIXTURE/scripts/lib/node-image.txt"
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
    grep -q "^${NEW_VERSION} ${NEW_DIGEST}$" "$FIXTURE/scripts/lib/node-image.txt"
}

@test "keeps the mode of every file it rewrites" {
    local files=(
        "$FIXTURE/docker/Dockerfile.ui"
        "$FIXTURE/TUTORIAL.md"
        "$FIXTURE/coffeeAGNTCY/coffee_agents/lungo/frontend/package.json"
        "$FIXTURE/coffeeAGNTCY/coffee_agents/lungo/frontend/package-lock.json"
    )
    local f
    for f in "${files[@]}"; do chmod 644 "$f"; done
    run_sync
    [ "$status" -eq 0 ]
    for f in "${files[@]}"; do
        [ -n "$(find "$f" -perm 644)" ]
    done
}

@test "leaves no temp files behind after a failure" {
    export TMPDIR="$BATS_TEST_TMPDIR/tmp"
    mkdir -p "$TMPDIR"
    printf '%s\n' 'Node.js is used for the UI.' >"$FIXTURE/TUTORIAL.md"
    run_sync
    [ "$status" -ne 0 ]
    [ -z "$(ls -A "$TMPDIR")" ]
}
