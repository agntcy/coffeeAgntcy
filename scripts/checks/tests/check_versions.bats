#!/usr/bin/env bats
# Mocked end-to-end test for check_versions.bash. The script cds to the
# repo that contains it (two levels above scripts/checks), so each test
# copies the script into a fixture repo and runs that copy.

SCRIPT="$BATS_TEST_DIRNAME/../check_versions.bash"

PIN="9.9.9"
OTHER_UV="1.2.3"
DIGEST="sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

setup() {
    REPO="$BATS_TEST_TMPDIR/repo"
    rm -rf "$REPO"
    build_passing
    mkdir -p "$REPO/scripts/checks"
    cp "$SCRIPT" "$REPO/scripts/checks/check_versions.bash"
    chmod +x "$REPO/scripts/checks/check_versions.bash"
}

build_passing() {
    mkdir -p \
        "$REPO/scripts/lib" \
        "$REPO/scripts" \
        "$REPO/docker" \
        "$REPO/.github/workflows" \
        "$REPO/coffeeAGNTCY/coffee_agents/corto" \
        "$REPO/coffeeAGNTCY/coffee_agents/lungo/frontend" \
        "$REPO/coffeeAGNTCY/coffee_agents/corto/exchange/frontend"
    cat >"$REPO/scripts/lib/versions.sh" <<EOF
NODE_VERSION="$PIN"
UV_VERSION="8.8.8"
EOF
    printf '%s %s\n' "$PIN" "$DIGEST" >"$REPO/scripts/lib/node-image.txt"
    cat >"$REPO/docker/Dockerfile.ui" <<EOF
ARG NODE_VERSION
FROM node:\${NODE_VERSION}-alpine@$DIGEST
EOF
    # A different uv than UV_VERSION. The check must ignore it.
    printf 'FROM astral/uv:%s-python3.13\n' "$OTHER_UV" >"$REPO/docker/Dockerfile.python-agent"
    printf 'echo "install \$NODE_VERSION"\n' >"$REPO/scripts/setup.sh"
    cat >"$REPO/.github/workflows/fe-ci.yaml" <<'EOF'
jobs:
  frontend-build:
    steps:
      - name: Read pinned Node version
        run: |
          . scripts/lib/versions.sh
          echo "version=${NODE_VERSION}" >> "$GITHUB_OUTPUT"
      - uses: actions/setup-node@sha
        with:
          node-version: ${{ steps.node-version.outputs.version }}
EOF
    cat >"$REPO/.github/workflows/docker-build-reusable.yaml" <<'EOF'
jobs:
  docker-build-and-push:
    steps:
      - run: |
          . scripts/lib/versions.sh
          if [ "$DOCKERFILE" = "docker/Dockerfile.ui" ]; then
            echo "arg=NODE_VERSION=${NODE_VERSION}" >> "$GITHUB_OUTPUT"
          fi
EOF
    cat >"$REPO/coffeeAGNTCY/coffee_agents/lungo/docker-compose.yaml" <<'EOF'
services:
  ui:
    build:
      dockerfile: docker/Dockerfile.ui
      args:
        NODE_VERSION: "${NODE_VERSION:?source scripts/env.sh so NODE_VERSION is set}"
EOF
    local dir
    for dir in \
        "$REPO/coffeeAGNTCY/coffee_agents/corto/exchange/frontend" \
        "$REPO/coffeeAGNTCY/coffee_agents/lungo/frontend"; do
        printf '{ "engines": { "node": ">=%s", "npm": ">=11.20.0" } }\n' "$PIN" >"$dir/package.json"
        printf '{ "packages": { "": { "engines": { "node": ">=%s" } } } }\n' "$PIN" >"$dir/package-lock.json"
        printf -- '- **Node.js** %s (`NODE_VERSION` in `scripts/lib/versions.sh`) or higher with **npm** 11.20.0 or higher\n' "$PIN" >"$dir/README.md"
    done
    local doc
    for doc in \
        "$REPO/TUTORIAL.md" \
        "$REPO/coffeeAGNTCY/coffee_agents/corto/README.md" \
        "$REPO/coffeeAGNTCY/coffee_agents/lungo/README.md"; do
        printf -- '- **Node.js** %s (`NODE_VERSION` in `scripts/lib/versions.sh`) or higher with **npm** 11.20.0 or higher\n' "$PIN" >"$doc"
    done
}

run_check() {
    run "$REPO/scripts/checks/check_versions.bash"
}

@test "passes when Node reads NODE_VERSION, including a drifted uv pin" {
    run_check
    [ "$status" -eq 0 ]
    [[ "$output" == *"Node consumers match NODE_VERSION ($PIN)"* ]]
}

@test "fails when a workflow sets a numeric node-version" {
    cat >"$REPO/.github/workflows/fe-ci.yaml" <<'EOF'
jobs:
  frontend-build:
    steps:
      - run: |
          . scripts/lib/versions.sh
          echo "version=${NODE_VERSION}" >> "$GITHUB_OUTPUT"
      - uses: actions/setup-node@sha
        with:
          node-version: "1.2.3"
EOF
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"literal"* ]]
}

@test "fails when the UI image uses a numeric node tag" {
    printf 'FROM node:1.2.3-alpine@%s\n' "$DIGEST" >"$REPO/docker/Dockerfile.ui"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"numeric node image tag"* ]]
}

@test "fails when the UI image digest disagrees with node-image.txt" {
    local other="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    printf 'ARG NODE_VERSION\nFROM node:${NODE_VERSION}-alpine@%s\n' "$other" >"$REPO/docker/Dockerfile.ui"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"does not match"* ]]
}

@test "fails when a compose UI build drops NODE_VERSION" {
    cat >"$REPO/coffeeAGNTCY/coffee_agents/lungo/docker-compose.yaml" <<'EOF'
services:
  ui:
    build:
      dockerfile: docker/Dockerfile.ui
      args:
        PROJECT_PATH: frontend
EOF
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"without passing NODE_VERSION"* ]]
}

@test "fails when engines.node is a different floor" {
    printf '{ "engines": { "node": ">=1.2.3" } }\n' >"$REPO/coffeeAGNTCY/coffee_agents/lungo/frontend/package.json"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"engines.node"* ]]
}

@test "fails when a doc states a different Node version" {
    printf -- '- **Node.js** 1.2.3 (`NODE_VERSION` in `scripts/lib/versions.sh`) or higher\n' >"$REPO/TUTORIAL.md"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"states Node.js 1.2.3"* ]]
}
