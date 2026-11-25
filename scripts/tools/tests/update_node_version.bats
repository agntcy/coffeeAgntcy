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
    printf 'FROM node:%s-alpine@%s\n' "$version" "$digest" >"$FIXTURE/docker/Dockerfile.ui"
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
