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
CHECKSUM="cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"

setup() {
    REPO="$BATS_TEST_TMPDIR/repo"
    rm -rf "$REPO"
    build_passing
    mkdir -p "$REPO/scripts/checks"
    cp "$SCRIPT" "$REPO/scripts/checks/check_versions.bash"
    chmod +x "$REPO/scripts/checks/check_versions.bash"
}

# Writes a checksums.txt that holds one line for every archive URL the
# fixture's pins produce, the way task tools:checksums would.
write_checksums() {
    (
        source "$REPO/scripts/lib/versions.sh"
        source "$REPO/scripts/lib/assets.sh"
        for tool in "${ASSET_TOOLS[@]}"; do
            for platform in "${SUPPORTED_PLATFORMS[@]}"; do
                asset_url "$tool" "${platform%-*}" "${platform#*-}"
            done
        done | LC_ALL=C sort -u | while IFS= read -r url; do
            printf '%s  %s\n' "$CHECKSUM" "$url"
        done
    ) >"$REPO/scripts/lib/checksums.txt"
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
ACTIONLINT_VERSION="1.7.7"
BATS_VERSION="1.11.0"
SHELLCHECK_VERSION="0.10.0"
SHFMT_VERSION="3.8.0"
TASK_VERSION="v3.40.0"
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
    # The real assets.sh: check_checksums reads the archive URLs from it.
    cp "$BATS_TEST_DIRNAME/../../lib/assets.sh" "$REPO/scripts/lib/assets.sh"
    write_checksums
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
      - name: Set up uv
        uses: astral-sh/setup-uv@sha # v10.2.0
        with:
          version: ${{ env.UV_VERSION }}
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
    [[ "$output" == *"All pinned tool versions match scripts/lib/versions.sh (node $PIN, uv 8.8.8, helm v4.3.0)"* ]]
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

@test "fails when setup-uv installs uv without a version input" {
    cat >"$REPO/.github/workflows/python-lint.yaml" <<'EOF'
jobs:
  ruff:
    steps:
      - run: |
          . scripts/lib/versions.sh
          echo "UV_VERSION=${UV_VERSION}" >> "$GITHUB_ENV"
      - name: Set up uv
        uses: astral-sh/setup-uv@sha # v10.2.0
      - name: Run Ruff
        run: uvx ruff check .
EOF
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"python-lint.yaml sets up uv without passing UV_VERSION"* ]]
}

@test "passes when setup-uv reads UV_VERSION from a step output" {
    cat >"$REPO/.github/workflows/python-lint.yaml" <<'EOF'
jobs:
  ruff:
    steps:
      - id: pins
        run: |
          . scripts/lib/versions.sh
          echo "UV_VERSION=${UV_VERSION}" >> "$GITHUB_OUTPUT"
      - uses: astral-sh/setup-uv@sha # v10.2.0
        with:
          version: ${{ steps.pins.outputs.UV_VERSION }}
EOF
    run_check
    [ "$status" -eq 0 ]
}

@test "fails when setup-uv reads a step output other than UV_VERSION" {
    cat >"$REPO/.github/workflows/python-lint.yaml" <<'EOF'
jobs:
  ruff:
    steps:
      - id: pins
        run: |
          . scripts/lib/versions.sh
          echo "UV_VERSION=${UV_VERSION}" >> "$GITHUB_OUTPUT"
      - uses: astral-sh/setup-uv@sha # v10.2.0
        with:
          version: ${{ steps.pins.outputs.OTHER }}
EOF
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"sets up uv without passing UV_VERSION"* ]]
}

@test "fails when setup-uv passes a literal version" {
    cat >"$REPO/.github/workflows/python-lint.yaml" <<'EOF'
jobs:
  ruff:
    steps:
      - run: |
          . scripts/lib/versions.sh
          echo "UV_VERSION=${UV_VERSION}" >> "$GITHUB_ENV"
      - uses: astral-sh/setup-uv@sha # v10.2.0
        with:
          version: "0.12.23"
EOF
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"sets up uv without passing UV_VERSION"* ]]
}

@test "fails when setup-uv reads UV_VERSION but the workflow never exports it" {
    cat >"$REPO/.github/workflows/python-lint.yaml" <<'EOF'
jobs:
  ruff:
    steps:
      - uses: astral-sh/setup-uv@sha # v10.2.0
        with:
          version: ${{ env.UV_VERSION }}
EOF
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"uses astral-sh/setup-uv without exporting UV_VERSION"* ]]
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

@test "passes when another action in the Helm workflow has a numeric version input" {
    cat >"$REPO/.github/workflows/helm-package-reusable.yaml" <<'EOF'
jobs:
  helm-package-and-push:
    steps:
      - uses: docker/setup-buildx-action@sha # v4.3.0
        with:
          version: v0.21.0
      - name: Read pinned Helm version
        run: |
          . scripts/lib/versions.sh
          version="${HELM_VERSION#v}"
      - uses: azure/setup-helm@sha
        with:
          version: ${{ steps.helm-version.outputs.version }}
      - name: Package Helm Chart
        run: |
          CHART_VERSION=$(grep '^version:' Chart.yaml | awk '{print $2}')
EOF
    run_check
    [ "$status" -eq 0 ]
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

@test "fails when a workflow uses an action that installs shellcheck" {
    printf '%s\n' 'steps:' '  - uses: ludeeus/action-shellcheck@sha # v2.0.0' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"uses an action that installs shellcheck"* ]]
}

@test "fails when a workflow installs shellcheck with a package manager and no version" {
    printf '%s\n' 'steps:' '  - run: sudo apt-get install -y shellcheck' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"installs shellcheck outside scripts/setup.sh"* ]]
}

@test "fails when a Dockerfile installs bats through npm" {
    printf '%s\n' 'FROM scratch' 'RUN npm install -g bats' >"$REPO/docker/Dockerfile.extra"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"Dockerfile.extra installs bats outside scripts/setup.sh"* ]]
}

@test "fails when a workflow go-installs task" {
    printf '%s\n' 'steps:' '  - run: go install github.com/go-task/task/v3/cmd/task@latest' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"lint.yaml installs task outside scripts/setup.sh"* ]]
}

@test "fails when a workflow runs the taskfile.dev install script" {
    printf '%s\n' 'steps:' '  - run: curl -sL https://taskfile.dev/install.sh | sh' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"downloads a toolchain tool outside scripts/setup.sh"* ]]
}

@test "passes when a workflow installs unrelated packages or only mentions a tool in a comment" {
    printf '%s\n' 'steps:' '  # do not apt-get install shellcheck here, setup.sh does it' '  - run: sudo apt-get install -y git curl' '  - run: pip install taskipy' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 0 ]
}

@test "passes when a tool name and an unrelated semver only share a line" {
    printf '%s\n' \
        'steps:' \
        '  - name: Lint with shellcheck, python 3.12.1' \
        '    run: echo hi' \
        >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 0 ]
}

@test "fails when a tool name is directly followed by a version" {
    printf '%s\n' 'steps:' '  - run: echo "bats-core 1.11.0 is required"' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"numeric version"* ]]
}

@test "fails when shellcheck is installed through pip at a version" {
    printf '%s\n' 'steps:' '  - run: pip install shellcheck-py==0.10.0.1' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"numeric version"* ]]
}

@test "fails when a tool and its version are separate words or a path" {
    printf '%s\n' 'steps:' '  - run: ./install-tools.sh shellcheck 0.10.0' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"numeric version"* ]]
    printf '%s\n' 'steps:' '  - run: curl -sSL https://example.com/shellcheck/0.10.0/sc.tgz | tar xz' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"numeric version"* ]]
}

@test "passes when only a trailing comment names a tool and a version" {
    printf '%s\n' \
        'steps:' \
        '  - run: task shell:lint # shellcheck 0.10.0 is pinned in setup.sh' \
        '  - run: task shell:lint # apt-get install shellcheck' \
        '  - uses: ./.github/actions/shellcheck-wrapper # v1.2.3' \
        >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 0 ]
}

@test "fails when a tool image is pinned with a colon version" {
    printf '%s\n' 'steps:' '  - run: docker run koalaman/shellcheck:v0.10.0 .' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"numeric version"* ]]
}

@test "fails when a tool is pinned with an at version" {
    printf '%s\n' 'steps:' '  - run: some-installer actionlint@1.7.7' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"numeric version"* ]]
}

@test "still fails when a pin is followed by a trailing comment" {
    printf '%s\n' 'steps:' '  - run: curl -O shellcheck-v1.2.3.linux.tar.gz # fetch it' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"numeric version"* ]]
}

@test "fails when a package manager flag sits between the manager and the verb" {
    printf '%s\n' 'steps:' '  - run: sudo apt-get -y install shellcheck' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"lint.yaml installs shellcheck outside scripts/setup.sh"* ]]
    printf '%s\n' 'FROM scratch' 'RUN apk --no-cache add shfmt' >"$REPO/docker/Dockerfile.extra"
    rm "$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"Dockerfile.extra installs shfmt outside scripts/setup.sh"* ]]
}

@test "fails when a package name sits on a continuation line" {
    printf '%s\n' 'steps:' '  - run: |' '      sudo apt-get install -y \' '        git \' '        shellcheck' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"lint.yaml installs shellcheck outside scripts/setup.sh"* ]]
}

@test "a comment ending in a backslash does not hide the next line" {
    printf '%s\n' 'steps:' '  # note \' '  - run: sudo apt-get install -y shellcheck' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"installs shellcheck outside scripts/setup.sh"* ]]
}

@test "fails when another package manager installs a tool" {
    printf '%s\n' 'steps:' '  - run: sudo snap install shellcheck' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"installs shellcheck outside scripts/setup.sh"* ]]
    printf '%s\n' 'steps:' '  - run: asdf install shfmt latest' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"installs shfmt outside scripts/setup.sh"* ]]
}

@test "fails when a workflow assigns a tool pin a literal" {
    printf '%s\n' 'env:' '  SHELLCHECK_VERSION: "0.10.0"' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"lint.yaml assigns SHELLCHECK_VERSION a literal"* ]]
}

@test "fails when a Dockerfile gives a tool pin a literal default" {
    printf '%s\n' 'FROM scratch' 'ARG TASK_VERSION=v3.40.0' >"$REPO/docker/Dockerfile.extra"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"Dockerfile.extra assigns TASK_VERSION a literal"* ]]
}

@test "passes when a tool pin is read, not assigned a literal" {
    printf '%s\n' 'steps:' '  - run: |' '      . scripts/lib/versions.sh' '      echo "SHELLCHECK_VERSION=${SHELLCHECK_VERSION}" >> "$GITHUB_ENV"' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 0 ]
}

@test "fails when Taskfile.yaml installs a tool outside setup.sh" {
    printf '%s\n' 'tasks:' '  tools:' '    cmds:' '      - apt-get install shellcheck' >"$REPO/Taskfile.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"Taskfile.yaml installs shellcheck outside scripts/setup.sh"* ]]
}

@test "fails when another script installs a tool, but setup.sh may" {
    printf '%s\n' '#!/usr/bin/env bash' 'apt-get install -y shellcheck' >"$REPO/scripts/other.sh"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"scripts/other.sh installs shellcheck outside scripts/setup.sh"* ]]
    rm "$REPO/scripts/other.sh"
    printf '%s\n' 'apt-get install -y shellcheck' >>"$REPO/scripts/setup.sh"
    run_check
    [ "$status" -eq 0 ]
}

@test "fails when a compose service runs a tool image at a version" {
    printf '%s\n' 'services:' '  sc:' '    image: koalaman/shellcheck:v0.10.0' >"$REPO/docker-compose.extra.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"docker-compose.extra.yaml installs a toolchain tool at a numeric version"* ]]
}

@test "fails when a pre-commit repo ships a tool" {
    printf '%s\n' 'repos:' '  - repo: https://github.com/shellcheck-py/shellcheck-py' '    rev: v0.10.0.1' >"$REPO/.pre-commit-config.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"uses a pre-commit repo that installs shellcheck"* ]]
}

@test "passes when a pre-commit repo is unrelated to the tools" {
    printf '%s\n' 'repos:' '  - repo: https://github.com/pre-commit/pre-commit-hooks' '    rev: v4.6.0' >"$REPO/.pre-commit-config.yaml"
    run_check
    [ "$status" -eq 0 ]
}

@test "ignores scripts under scripts/checks" {
    mkdir -p "$REPO/scripts/checks"
    printf '%s\n' 'apt-get install shellcheck' >"$REPO/scripts/checks/example.sh"
    run_check
    [ "$status" -eq 0 ]
}

@test "fails when a pin is bumped and checksums.txt is not regenerated" {
    sed -i.bak 's/^HELM_VERSION=.*/HELM_VERSION="v4.4.0"/' "$REPO/scripts/lib/versions.sh"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"checksums.txt has no checksum for https://get.helm.sh/helm-v4.4.0-linux-amd64.tar.gz"* ]]
    [[ "$output" == *"checksums.txt has a line for https://get.helm.sh/helm-v4.3.0-linux-amd64.tar.gz"* ]]
}

@test "passes once checksums.txt is regenerated after a bump" {
    sed -i.bak 's/^SHELLCHECK_VERSION=.*/SHELLCHECK_VERSION="0.11.0"/' "$REPO/scripts/lib/versions.sh"
    write_checksums
    run_check
    [ "$status" -eq 0 ]
}

@test "fails when checksums.txt has a line no pin produces" {
    printf '%s  %s\n' "$CHECKSUM" "https://example.com/old-tool.tar.gz" >>"$REPO/scripts/lib/checksums.txt"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"has a line for https://example.com/old-tool.tar.gz"* ]]
}

@test "fails when a checksums.txt hash is not 64 hex characters" {
    sed -i.bak 's/^[0-9a-f]*  \(https:\/\/nodejs.org.*linux-x64.*\)$/abc123  \1/' "$REPO/scripts/lib/checksums.txt"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"checksums.txt has no checksum for https://nodejs.org/dist/v9.9.9/node-v9.9.9-linux-x64.tar.gz"* ]]
}

@test "fails when checksums.txt is missing" {
    rm "$REPO/scripts/lib/checksums.txt"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"scripts/lib/checksums.txt is missing"* ]]
}

@test "ignores a commented-out tool action" {
    printf '%s\n' 'steps:' '  # - uses: ludeeus/action-shellcheck@sha' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 0 ]
}

@test "ignores a local action whose name contains a tool name" {
    printf '%s\n' 'steps:' '  - uses: ./.github/actions/run-shellcheck-via-task' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 0 ]
}

@test "fails when a workflow uses arduino/setup-task" {
    printf '%s\n' 'steps:' '  - uses: arduino/setup-task@sha # v2.0.0' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"uses an action that installs task"* ]]
}

@test "fails when an action name differs only by case" {
    printf '%s\n' 'steps:' '  - uses: Ludeeus/Action-ShellCheck@sha' >"$REPO/.github/workflows/lint.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"uses an action that installs shellcheck"* ]]
}

@test "fails when a composite action under .github/actions uses a tool action" {
    mkdir -p "$REPO/.github/actions/lint"
    printf '%s\n' 'runs:' '  steps:' '    - uses: mig4/setup-bats@sha' >"$REPO/.github/actions/lint/action.yml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *".github/actions/lint/action.yml uses an action that installs bats"* ]]
}

@test "fails when a Dockerfile outside docker/ installs shellcheck" {
    mkdir -p "$REPO/svc"
    printf '%s\n' 'FROM scratch' 'RUN apk add shellcheck' >"$REPO/svc/app.Dockerfile"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"app.Dockerfile installs shellcheck outside scripts/setup.sh"* ]]
}

@test "fails when an inline flow-mapping setup-helm step passes a literal" {
    printf '%s\n' 'jobs:' '  j:' '    steps:' '      - { uses: azure/setup-helm@sha, with: { version: 4.3.0 } }' >"$REPO/.github/workflows/other.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"other.yaml sets Helm version to a literal"* ]]
}

@test "fails when a setup-helm step lists with: before uses: and passes a literal" {
    printf '%s\n' 'jobs:' '  j:' '    steps:' '      - with:' '          version: "4.3"' '        uses: "azure/setup-helm@sha"' >"$REPO/.github/workflows/other.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"other.yaml sets Helm version to a literal"* ]]
}

@test "fails when a setup-helm step has no version input" {
    printf '%s\n' 'jobs:' '  j:' '    steps:' '      - uses: azure/setup-helm@sha' >"$REPO/.github/workflows/other.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"other.yaml calls azure/setup-helm without a version input"* ]]
}

@test "fails when setup-helm version is latest" {
    printf '%s\n' 'jobs:' '  j:' '    steps:' '      - uses: azure/setup-helm@sha' '        with:' '          version: latest' >"$REPO/.github/workflows/other.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"other.yaml sets Helm version to something other than HELM_VERSION"* ]]
}

@test "fails when a workflow assigns HELM_VERSION a literal" {
    printf '%s\n' 'env:' '  HELM_VERSION: v4.3.0' >"$REPO/.github/workflows/other.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"other.yaml assigns HELM_VERSION a literal"* ]]
}

@test "fails when the Helm workflow only mentions versions.sh in a comment" {
    printf '%s\n' '# . scripts/lib/versions.sh' 'jobs:' '  j:' '    steps:' '      - run: echo HELM_VERSION' >"$REPO/.github/workflows/helm-package-reusable.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"does not source scripts/lib/versions.sh"* ]]
}

@test "fails when setup-node has no node-version input" {
    printf '%s\n' 'jobs:' '  j:' '    steps:' '      - run: . scripts/lib/versions.sh; echo $NODE_VERSION' '      - uses: actions/setup-node@sha' >"$REPO/.github/workflows/other.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"other.yaml calls actions/setup-node without a node-version input"* ]]
}

@test "fails when setup-node reads node-version-file" {
    printf '%s\n' 'jobs:' '  j:' '    steps:' '      - run: . scripts/lib/versions.sh; echo $NODE_VERSION' '      - uses: actions/setup-node@sha' '        with:' '          node-version-file: .nvmrc' >"$REPO/.github/workflows/other.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"uses node-version-file for actions/setup-node"* ]]
}

@test "fails when setup-node gets a v-prefixed literal" {
    printf '%s\n' 'jobs:' '  j:' '    steps:' '      - run: . scripts/lib/versions.sh; echo $NODE_VERSION' '      - uses: actions/setup-node@sha' '        with:' '          node-version: v26.13.1' >"$REPO/.github/workflows/other.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"other.yaml sets node-version to a literal"* ]]
}

@test "fails when setup-node reads a matrix value" {
    printf '%s\n' 'jobs:' '  j:' '    steps:' '      - run: . scripts/lib/versions.sh; echo $NODE_VERSION' '      - uses: actions/setup-node@sha' '        with:' '          node-version: ${{ matrix.node }}' >"$REPO/.github/workflows/other.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"other.yaml sets node-version to something other than NODE_VERSION"* ]]
}

@test "fails when a workflow installs Node through nvm at a literal version" {
    printf '%s\n' 'jobs:' '  j:' '    steps:' '      - run: nvm install 20.1.0' >"$REPO/.github/workflows/other.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"installs Node through a version manager"* ]]
}

@test "ignores a commented-out node-version literal" {
    printf '%s\n' 'jobs:' '  j:' '    steps:' '      # node-version: "20"' '      - run: echo hi' >"$REPO/.github/workflows/other.yaml"
    run_check
    [ "$status" -eq 0 ]
}

@test "fails when a Dockerfile pins a numeric node tag behind --platform and a registry prefix" {
    printf '%s\n' 'FROM --platform=$BUILDPLATFORM docker.io/library/node:22-alpine' >"$REPO/docker/Dockerfile.extra"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"Dockerfile.extra pins a numeric node image tag"* ]]
}

@test "passes when another Node image variant carries its own digest" {
    mkdir -p "$REPO/svc"
    printf '%s\n' 'ARG NODE_VERSION' 'FROM node:${NODE_VERSION}-bookworm@sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc' >"$REPO/svc/Dockerfile"
    run_check
    [ "$status" -eq 0 ]
}

@test "fails when the pytest workflow exports the pins only in comments" {
    printf '%s\n' 'jobs:' '  run-tests:' '    steps:' '      # . scripts/lib/versions.sh' '      # echo "NODE_VERSION=${NODE_VERSION}" >> "$GITHUB_ENV"' '      # echo "UV_VERSION=${UV_VERSION}" >> "$GITHUB_ENV"' >"$REPO/.github/workflows/test-reusable.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"test-reusable.yaml does not source scripts/lib/versions.sh"* ]]
    [[ "$output" == *"does not export NODE_VERSION"* ]]
    [[ "$output" == *"does not export UV_VERSION"* ]]
}

@test "fails when a compose file gives NODE_VERSION a default" {
    cat >"$REPO/coffeeAGNTCY/coffee_agents/lungo/docker-compose.yaml" <<'EOF'
services:
  ui:
    build:
      dockerfile: docker/Dockerfile.ui
      args:
        NODE_VERSION: "${NODE_VERSION:-26.13.1}"
EOF
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"gives NODE_VERSION a default or a literal"* ]]
}

@test "fails when a compose file passes a list-form literal" {
    cat >"$REPO/coffeeAGNTCY/coffee_agents/lungo/docker-compose.yaml" <<'EOF'
services:
  ui:
    build:
      dockerfile: docker/Dockerfile.ui
      args:
        - NODE_VERSION=26.13.1
EOF
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"gives NODE_VERSION a default or a literal"* ]]
}

@test "fails when one service in a compose file leaves out the build arg" {
    cat >"$REPO/coffeeAGNTCY/coffee_agents/lungo/docker-compose.yaml" <<'EOF'
services:
  ui:
    build:
      dockerfile: docker/Dockerfile.ui
      args:
        NODE_VERSION: "${NODE_VERSION:?set it}"
  ui2:
    build:
      context: .
      dockerfile: docker/Dockerfile.ui
EOF
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"docker-compose.yaml:8 builds docker/Dockerfile.ui without passing NODE_VERSION"* ]]
}

@test "fails when a compose build passes the arg without the :? guard" {
    cat >"$REPO/coffeeAGNTCY/coffee_agents/lungo/docker-compose.yaml" <<'EOF'
services:
  ui:
    build:
      dockerfile: docker/Dockerfile.ui
      args:
        NODE_VERSION: "${NODE_VERSION}"
EOF
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"passes NODE_VERSION without \${NODE_VERSION:?...}"* ]]
}

@test "passes when the build args come before dockerfile in a compose build block" {
    cat >"$REPO/coffeeAGNTCY/coffee_agents/lungo/docker-compose.yaml" <<'EOF'
services:
  ui:
    build:
      args:
        NODE_VERSION: "${NODE_VERSION:?set it}"
      dockerfile: docker/Dockerfile.ui
EOF
    run_check
    [ "$status" -eq 0 ]
}

@test "fails when docker-build-reusable assigns a quoted NODE_VERSION literal" {
    printf '%s\n' 'jobs:' '  j:' '    steps:' '      - run: |' '          . scripts/lib/versions.sh' '          echo "arg=NODE_VERSION=${NODE_VERSION}" ; docker/Dockerfile.ui docker/Dockerfile.python-agent UV_VERSION=${UV_VERSION}' '          NODE_VERSION="26.13.1"' >"$REPO/.github/workflows/docker-build-reusable.yaml"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"docker-build-reusable.yaml assigns NODE_VERSION a literal"* ]]
}

@test "fails when the root engines floor is missing and a dependency has one" {
    printf '%s\n' '{' '  "packages": {' '    "": {' '      "engines": { "node": "^9.9.9" }' '    },' '    "node_modules/x": {' "      \"engines\": { \"node\": \">=$PIN\" }" '    }' '  }' '}' >"$REPO/coffeeAGNTCY/coffee_agents/lungo/frontend/package-lock.json"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"lungo/frontend/package-lock.json has no root engines.node floor"* ]]
}

@test "fails when an OpenSpec skill has no generatedBy stamp" {
    mkdir -p "$REPO/.agents/skills/openspec-explore"
    printf -- '---\nname: x\n---\n' >"$REPO/.agents/skills/openspec-explore/SKILL.md"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"openspec-explore/SKILL.md is missing a generatedBy stamp"* ]]
}

@test "fails when an OpenSpec skill stamp is unquoted and stale" {
    mkdir -p "$REPO/.agents/skills/openspec-explore"
    printf -- '---\nmetadata:\n  generatedBy: 0.0.1\n---\n' >"$REPO/.agents/skills/openspec-explore/SKILL.md"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"generatedBy is 0.0.1, OPENSPEC_VERSION is $OPENSPEC_PIN"* ]]
}

@test "passes when an OpenSpec skill stamp is single-quoted and current" {
    mkdir -p "$REPO/.agents/skills/openspec-explore"
    printf -- "---\nmetadata:\n  generatedBy: '%s'\n---\n" "$OPENSPEC_PIN" >"$REPO/.agents/skills/openspec-explore/SKILL.md"
    run_check
    [ "$status" -eq 0 ]
}

@test "reads the install sentence, not an earlier versionless Node.js mention" {
    printf '%s\n' 'Node.js powers the UI.' "- **Node.js** $PIN (\`NODE_VERSION\` in \`scripts/lib/versions.sh\`) or higher" >"$REPO/TUTORIAL.md"
    run_check
    [ "$status" -eq 0 ]
}

@test "fails when no line is a Node.js install sentence" {
    printf '%s\n' "Node.js $PIN is used for the UI (\`NODE_VERSION\` in \`scripts/lib/versions.sh\`)." >"$REPO/TUTORIAL.md"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"TUTORIAL.md has no Node.js install sentence"* ]]
}

@test "fails when a doc states a different Node version" {
    printf -- '- **Node.js** 1.2.3 (`NODE_VERSION` in `scripts/lib/versions.sh`) or higher\n' >"$REPO/TUTORIAL.md"
    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"states Node.js 1.2.3"* ]]
}
