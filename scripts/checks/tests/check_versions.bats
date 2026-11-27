#!/usr/bin/env bats
# Mocked end-to-end test for check_versions.bash. The script cds to the
# repo that contains it (two levels above scripts/checks), so each test
# copies the script into a fixture repo and runs that copy.

SCRIPT="$BATS_TEST_DIRNAME/../check_versions.bash"

PIN="9.9.9"
OTHER_UV="1.2.3"
OPENSPEC_PIN="3.3.3"
RENOVATE_PIN="4.4.4"
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
        "$REPO/scripts/lib/npm-tools" \
        "$REPO/coffeeAGNTCY/coffee_agents/corto" \
        "$REPO/coffeeAGNTCY/coffee_agents/lungo/frontend" \
        "$REPO/coffeeAGNTCY/coffee_agents/corto/exchange/frontend"
    cat >"$REPO/scripts/lib/versions.sh" <<EOF
NODE_VERSION="$PIN"
UV_VERSION="8.8.8"
HELM_VERSION="v4.3.0"
OPENSPEC_VERSION="$OPENSPEC_PIN"
RENOVATE_VERSION="$RENOVATE_PIN"
EOF
    printf '%s %s\n' "$PIN" "$DIGEST" >"$REPO/scripts/lib/node-image.txt"
    printf '%s %s\n' "8.8.8" "$DIGEST" >"$REPO/scripts/lib/uv-image.txt"
    cat >"$REPO/docker/Dockerfile.ui" <<EOF
ARG NODE_VERSION
FROM node:\${NODE_VERSION}-alpine@$DIGEST
EOF
    cat >"$REPO/docker/Dockerfile.python-agent" <<EOF
ARG UV_VERSION
FROM astral/uv:\${UV_VERSION}-python3.13-trixie-slim@$DIGEST
EOF
    printf 'echo "$NODE_VERSION $ACTIONLINT_VERSION $BATS_VERSION $SHELLCHECK_VERSION $SHFMT_VERSION $TASK_VERSION"\n' >"$REPO/scripts/setup.sh"
    printf 'echo "${ACTIONLINT_VERSION} ${BATS_VERSION} ${SHELLCHECK_VERSION} ${SHFMT_VERSION} ${TASK_VERSION}"\n' >"$REPO/scripts/lib/assets.sh"
    cat >"$REPO/scripts/lib/npm-tools/package-lock.json" <<EOF
{
  "packages": {
    "": {
      "dependencies": {
        "@fission-ai/openspec": "$OPENSPEC_PIN",
        "renovate": "$RENOVATE_PIN"
      }
    }
  }
}
EOF
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
          elif [ "$DOCKERFILE" = "docker/Dockerfile.python-agent" ]; then
            echo "arg=UV_VERSION=${UV_VERSION}" >> "$GITHUB_OUTPUT"
          fi
EOF
    cat >"$REPO/.github/workflows/test-reusable.yaml" <<'EOF'
jobs:
  run-tests:
    steps:
      - name: Export image build pins
        run: |
          . scripts/lib/versions.sh
          echo "NODE_VERSION=${NODE_VERSION}" >> "$GITHUB_ENV"
          echo "UV_VERSION=${UV_VERSION}" >> "$GITHUB_ENV"
EOF
    cat >"$REPO/.github/workflows/helm-package-reusable.yaml" <<'EOF'
jobs:
  helm-package-and-push:
    steps:
      - uses: docker/setup-buildx-action@sha # v4.3.0
      - name: Read pinned Helm version
        run: |
          . scripts/lib/versions.sh
          version="${HELM_VERSION#v}"
          echo "version=${version}" >> "$GITHUB_OUTPUT"
      - uses: azure/setup-helm@sha
        with:
          version: ${{ steps.helm-version.outputs.version }}
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

@test "passes when every pin reads versions.sh, including a buildx v4.3.0 comment" {
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

@test "fails when the Python image uses a numeric uv tag" {
    printf 'FROM astral/uv:%s-python3.13-trixie-slim@%s\n' "$OTHER_UV" "$DIGEST" >"$REPO/docker/Dockerfile.python-agent"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"numeric uv image tag"* ]]
}

@test "fails when the uv image digest disagrees with uv-image.txt" {
    local other="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    printf 'ARG UV_VERSION\nFROM astral/uv:${UV_VERSION}-python3.13-trixie-slim@%s\n' "$other" >"$REPO/docker/Dockerfile.python-agent"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"does not match"* ]]
}

@test "fails when Python tests do not export the image pins" {
    cat >"$REPO/.github/workflows/test-reusable.yaml" <<'EOF'
jobs:
  run-tests:
    steps:
      - name: Run tests
        run: uv run pytest
EOF
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"test-reusable.yaml does not source scripts/lib/versions.sh"* ]]
    [[ "$output" == *"does not export NODE_VERSION"* ]]
    [[ "$output" == *"does not export UV_VERSION"* ]]
}

@test "fails when a compose Python build drops UV_VERSION" {
    cat >"$REPO/coffeeAGNTCY/coffee_agents/corto/docker-compose.yaml" <<'EOF'
services:
  farm:
    build:
      dockerfile: docker/Dockerfile.python-agent
      args:
        PROJECT_PATH: corto
EOF
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"without passing UV_VERSION"* ]]
}

@test "fails when Helm CI sets a numeric version" {
    cat >"$REPO/.github/workflows/helm-package-reusable.yaml" <<'EOF'
jobs:
  helm-package-and-push:
    steps:
      - uses: docker/setup-buildx-action@sha # v4.3.0
      - run: |
          . scripts/lib/versions.sh
          version="${HELM_VERSION#v}"
      - uses: azure/setup-helm@sha
        with:
          version: "4.3.0"
EOF
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"literal"* ]]
}

@test "fails when the npm lockfile disagrees with the openspec pin" {
    printf '{ "packages": { "": { "dependencies": { "@fission-ai/openspec": "0.0.1", "renovate": "%s" } } } }\n' "$RENOVATE_PIN" >"$REPO/scripts/lib/npm-tools/package-lock.json"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"OPENSPEC_VERSION"* ]]
}

@test "fails when an OpenSpec skill stamp disagrees" {
    mkdir -p "$REPO/.agents/skills/openspec-propose"
    printf '%s\n' '---' 'generatedBy: "0.0.1"' '---' >"$REPO/.agents/skills/openspec-propose/SKILL.md"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"generatedBy"* ]]
}

@test "fails when a workflow installs shellcheck at a number" {
    printf 'run: curl -O shellcheck-v1.2.3.linux.tar.gz\n' >"$REPO/.github/workflows/shellcheck.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"numeric version"* ]]
}

@test "fails when a doc states a different Node version" {
    printf -- '- **Node.js** 1.2.3 (`NODE_VERSION` in `scripts/lib/versions.sh`) or higher\n' >"$REPO/TUTORIAL.md"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"states Node.js 1.2.3"* ]]
}
