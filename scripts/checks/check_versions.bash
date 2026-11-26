#!/usr/bin/env bash
# Fails when a Node install does not read NODE_VERSION from
# scripts/lib/versions.sh, or when a consumer that cannot read the
# variable (UI image digest, frontend engines.node, the docs that state
# the Node version) disagrees with it.
#
# One function per versions.sh pin. Today that is check_node only.
# Other pins are not checked. uv is a known gap: docker/Dockerfile.python-agent
# can name a different uv than UV_VERSION until a later change adds check_uv.
#
# Usage: scripts/checks/check_versions.bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

# shellcheck source=scripts/lib/versions.sh
source "$REPO_ROOT/scripts/lib/versions.sh"

NODE_IMAGE_FILE="scripts/lib/node-image.txt"
# Literal markdown backticks, and the ${NODE_VERSION} text callers write.
# Neither is a shell expansion. shellcheck disable applies to the next command.
# shellcheck disable=SC2016
MARKER='(`NODE_VERSION` in `scripts/lib/versions.sh`)'
# shellcheck disable=SC2016
NODE_EXPANSION='${NODE_VERSION}'
# shellcheck disable=SC2016
NODE_EXPANSION_OPEN='${NODE_VERSION'

DOC_FILES=(
    "TUTORIAL.md"
    "coffeeAGNTCY/coffee_agents/corto/README.md"
    "coffeeAGNTCY/coffee_agents/lungo/README.md"
    "coffeeAGNTCY/coffee_agents/corto/exchange/frontend/README.md"
    "coffeeAGNTCY/coffee_agents/lungo/frontend/README.md"
)

ENGINE_FILES=(
    "coffeeAGNTCY/coffee_agents/corto/exchange/frontend/package.json"
    "coffeeAGNTCY/coffee_agents/corto/exchange/frontend/package-lock.json"
    "coffeeAGNTCY/coffee_agents/lungo/frontend/package.json"
    "coffeeAGNTCY/coffee_agents/lungo/frontend/package-lock.json"
)

failed=0

report() {
    echo "$*" >&2
    failed=1
}

first_node_semver() {
    local file="$1" line
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" == *"Node.js"* ]]; then
            if [[ "$line" =~ [0-9]+\.[0-9]+\.[0-9]+ ]]; then
                printf '%s' "${BASH_REMATCH[0]}"
                return 0
            fi
            return 1
        fi
    done <"$file"
    return 1
}

first_node_engine() {
    local file="$1" line
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" =~ \"node\":\ \"(>=[0-9]+\.[0-9]+\.[0-9]+)\" ]]; then
            printf '%s' "${BASH_REMATCH[1]}"
            return 0
        fi
    done <"$file"
    return 1
}

read_record() {
    RECORD_VERSION=""
    RECORD_DIGEST=""
    [[ -f "$NODE_IMAGE_FILE" ]] || {
        report "$NODE_IMAGE_FILE is missing"
        return 1
    }
    local line count=0 version digest
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ "$line" =~ ^# ]] && continue
        [[ -z "$line" ]] && continue
        if [[ "$line" =~ ^([0-9]+\.[0-9]+\.[0-9]+)[[:space:]]+(sha256:[0-9a-f]{64})$ ]]; then
            version="${BASH_REMATCH[1]}"
            digest="${BASH_REMATCH[2]}"
            count=$((count + 1))
        else
            report "$NODE_IMAGE_FILE has a line that is not '<version> sha256:<64-hex>': $line"
            return 1
        fi
    done <"$NODE_IMAGE_FILE"
    if [[ "$count" -ne 1 ]]; then
        report "$NODE_IMAGE_FILE must contain exactly one digest line"
        return 1
    fi
    RECORD_VERSION="$version"
    RECORD_DIGEST="$digest"
}

check_workflows() {
    local file line
    [[ -d .github/workflows ]] || {
        report ".github/workflows is missing"
        return 0
    }
    while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        grep -q 'node-version:' "$file" || continue
        if grep -Eq 'node-version:[[:space:]]*["'\'']?[0-9]' "$file"; then
            report "$file sets node-version to a literal. Source scripts/lib/versions.sh and pass NODE_VERSION."
        fi
        if ! grep -Fq 'scripts/lib/versions.sh' "$file"; then
            report "$file sets node-version without sourcing scripts/lib/versions.sh"
        fi
        if ! grep -Fq 'NODE_VERSION' "$file"; then
            report "$file sets node-version without reading NODE_VERSION"
        fi
    done < <(find .github/workflows -type f \( -name '*.yml' -o -name '*.yaml' \) -not -path '*/node_modules/*' | sort)
}

check_images() {
    local digest="$1" file line found
    while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        found=0
        while IFS= read -r line || [[ -n "$line" ]]; do
            [[ "$line" =~ ^[[:space:]]*FROM[[:space:]]+node: || "$line" =~ ^[[:space:]]*image:[[:space:]]*[\"\']?node: ]] || continue
            found=1
            if [[ "$line" =~ node:[0-9] ]]; then
                report "$file pins a numeric node image tag. Use ${NODE_EXPANSION} from scripts/lib/versions.sh."
            elif [[ "$line" != *"$NODE_EXPANSION"* ]]; then
                report "$file has a node image that does not use ${NODE_EXPANSION}"
            fi
            if [[ "$line" =~ @(sha256:[0-9a-f]{64}) ]]; then
                if [[ "${BASH_REMATCH[1]}" != "$digest" ]]; then
                    report "$file digest ${BASH_REMATCH[1]} does not match $NODE_IMAGE_FILE ($digest)"
                fi
            else
                report "$file node image has no @sha256 digest"
            fi
        done <"$file"
        if [[ "${file#./}" == "docker/Dockerfile.ui" && "$found" -eq 0 ]]; then
            report "docker/Dockerfile.ui does not install node from NODE_VERSION"
        fi
    done < <(find . -type f \( -name 'Dockerfile' -o -name 'Dockerfile.*' -o -name '*.Dockerfile' -o -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' -o -name 'compose.yml' -o -name 'compose.yaml' \) -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/.tools/*' | sort)
}

check_ui_callers() {
    local file
    while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        grep -Fq 'docker/Dockerfile.ui' "$file" || continue
        if ! grep -Fq 'NODE_VERSION' "$file"; then
            report "$file builds docker/Dockerfile.ui without passing NODE_VERSION"
            continue
        fi
        if grep -Eq 'NODE_VERSION:[[:space:]]*["'\'']?[0-9]+\.[0-9]+\.[0-9]+' "$file"; then
            report "$file assigns NODE_VERSION a literal. Pass the variable."
        fi
        if ! grep -Fq "$NODE_EXPANSION_OPEN" "$file"; then
            report "$file mentions NODE_VERSION but does not expand ${NODE_EXPANSION}"
        fi
    done < <(find . -type f \( -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' -o -name 'compose.yml' -o -name 'compose.yaml' \) -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/.tools/*' | sort)

    local reusable=".github/workflows/docker-build-reusable.yaml"
    if [[ ! -f "$reusable" ]]; then
        report "$reusable is missing; CI UI builds must inject NODE_VERSION"
        return 0
    fi
    if ! grep -Fq 'scripts/lib/versions.sh' "$reusable"; then
        report "$reusable does not source scripts/lib/versions.sh"
    fi
    if ! grep -Fq 'docker/Dockerfile.ui' "$reusable"; then
        report "$reusable does not limit the Node build-arg to docker/Dockerfile.ui"
    fi
    if ! grep -Fq "NODE_VERSION=$NODE_EXPANSION" "$reusable"; then
        report "$reusable does not pass NODE_VERSION from scripts/lib/versions.sh"
    fi
    if grep -Eq 'NODE_VERSION=[0-9]' "$reusable"; then
        report "$reusable assigns NODE_VERSION a literal"
    fi
}

check_setup() {
    local setup="scripts/setup.sh"
    if [[ ! -f "$setup" ]]; then
        report "$setup is missing"
        return 0
    fi
    # shellcheck disable=SC2016
    if ! grep -Fq '$NODE_VERSION' "$setup" && ! grep -Fq '${NODE_VERSION}' "$setup"; then
        report "$setup no longer installs Node from NODE_VERSION"
    fi
    if grep -Eq 'node-v[0-9]' "$setup"; then
        report "$setup hardcodes a node-v<version> directory"
    fi
}

check_engines() {
    local file got
    for file in "${ENGINE_FILES[@]}"; do
        if [[ ! -f "$file" ]]; then
            report "$file is missing"
            continue
        fi
        if ! got="$(first_node_engine "$file")"; then
            report "$file has no root engines.node floor"
            continue
        fi
        if [[ "$got" != ">=$NODE_VERSION" ]]; then
            report "$file engines.node is $got, want >=$NODE_VERSION"
        fi
    done
}

check_docs() {
    local file got
    for file in "${DOC_FILES[@]}"; do
        if [[ ! -f "$file" ]]; then
            report "$file is missing"
            continue
        fi
        if ! got="$(first_node_semver "$file")"; then
            report "$file has no Node.js install sentence"
            continue
        fi
        if [[ "$got" != "$NODE_VERSION" ]]; then
            report "$file states Node.js $got, NODE_VERSION is $NODE_VERSION"
        fi
        if ! grep -Fq "$MARKER" "$file"; then
            report "$file Node.js sentence does not name NODE_VERSION in scripts/lib/versions.sh"
        fi
    done
}

check_node() {
    if ! read_record; then
        return 0
    fi
    if [[ "$RECORD_VERSION" != "$NODE_VERSION" ]]; then
        report "$NODE_IMAGE_FILE records $RECORD_VERSION, NODE_VERSION is $NODE_VERSION"
    fi
    check_workflows
    check_images "$RECORD_DIGEST"
    check_ui_callers
    check_setup
    check_engines
    check_docs
}

check_node

if [[ "$failed" -ne 0 ]]; then
    exit 1
fi
echo "Node consumers match NODE_VERSION ($NODE_VERSION)."
