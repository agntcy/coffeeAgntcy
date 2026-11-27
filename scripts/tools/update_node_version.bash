#!/usr/bin/env bash
# Rewrites the Node consumers that cannot read NODE_VERSION themselves so
# they match scripts/lib/versions.sh, and records the UI base image
# manifest-list digest those consumers pin.
#
# Reads NODE_VERSION. Fetches the node:<NODE_VERSION>-alpine manifest-list
# digest when scripts/lib/node-image.txt is missing or names a different
# version. Rewrites that record, the @sha256: in docker/Dockerfile.ui, the
# root engines.node floor in both frontend package.json files and their
# lockfiles, and the Node install sentence in the five docs listed below.
# Exits 0 without network when the record already matches and those
# consumers already agree.
#
# NODE_IMAGE_DIGEST, when set, is used instead of a registry fetch (tests).
# REPO_ROOT, when set, is the tree to edit (tests). Otherwise the repo that
# contains this script.
#
# Usage: scripts/tools/update_node_version.bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "${REPO_ROOT:-}" ]]; then
    REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

# shellcheck source=scripts/lib/versions.sh
source "$REPO_ROOT/scripts/lib/versions.sh"

NODE_IMAGE_FILE="$REPO_ROOT/scripts/lib/node-image.txt"
DOCKERFILE="$REPO_ROOT/docker/Dockerfile.ui"
# Literal markdown backticks: the marker the version check looks for.
# shellcheck disable=SC2016
MARKER='(`NODE_VERSION` in `scripts/lib/versions.sh`)'

DOC_FILES=(
    "$REPO_ROOT/TUTORIAL.md"
    "$REPO_ROOT/coffeeAGNTCY/coffee_agents/corto/README.md"
    "$REPO_ROOT/coffeeAGNTCY/coffee_agents/lungo/README.md"
    "$REPO_ROOT/coffeeAGNTCY/coffee_agents/corto/exchange/frontend/README.md"
    "$REPO_ROOT/coffeeAGNTCY/coffee_agents/lungo/frontend/README.md"
)

ENGINE_FILES=(
    "$REPO_ROOT/coffeeAGNTCY/coffee_agents/corto/exchange/frontend/package.json"
    "$REPO_ROOT/coffeeAGNTCY/coffee_agents/corto/exchange/frontend/package-lock.json"
    "$REPO_ROOT/coffeeAGNTCY/coffee_agents/lungo/frontend/package.json"
    "$REPO_ROOT/coffeeAGNTCY/coffee_agents/lungo/frontend/package-lock.json"
)

die() {
    echo "error: $*" >&2
    exit 1
}

# Scratch space for the rewrites. A rewrite is built here and copied over
# the target with cat, so the target keeps its own mode (mktemp files are
# 0600 and mv would carry that onto the file), and a die leaves nothing
# behind.
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# First semver on the install sentence: the first line that has Node.js, a
# semver, and " or higher". An earlier versionless Node.js mention is not
# the sentence.
first_node_semver() {
    local file="$1" line
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" == *"Node.js"* && "$line" == *" or higher"* && "$line" =~ [0-9]+\.[0-9]+\.[0-9]+ ]]; then
            printf '%s' "${BASH_REMATCH[0]}"
            return 0
        fi
    done <"$file"
    return 1
}

doc_has_marker() {
    local file="$1" line
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" == *"Node.js"* && "$line" == *"$MARKER"* ]]; then
            return 0
        fi
    done <"$file"
    return 1
}

# First "node": ">=x.y.z" value, which is the root package in both
# package.json and a lockfileVersion 3 lockfile. Later copies belong to
# dependencies and are left alone. The scan stops at the first
# node_modules/ entry, so a root entry without a floor is an error rather
# than a match on a dependency's engines.
first_node_engine() {
    local file="$1" line
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ "$line" == *'"node_modules/'* ]] && return 1
        if [[ "$line" =~ \"node\":[[:space:]]*\"(>=[0-9]+\.[0-9]+\.[0-9]+)\" ]]; then
            printf '%s' "${BASH_REMATCH[1]}"
            return 0
        fi
    done <"$file"
    return 1
}

dockerfile_digest() {
    local line
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" =~ ^FROM[[:space:]]+node:.*@(sha256:[0-9a-f]{64}) ]]; then
            printf '%s' "${BASH_REMATCH[1]}"
            return 0
        fi
    done <"$DOCKERFILE"
    return 1
}

read_record() {
    RECORD_VERSION=""
    RECORD_DIGEST=""
    [[ -f "$NODE_IMAGE_FILE" ]] || return 0
    local line count=0 version digest
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ "$line" =~ ^# ]] && continue
        [[ -z "$line" ]] && continue
        if [[ "$line" =~ ^([0-9]+\.[0-9]+\.[0-9]+)[[:space:]]+(sha256:[0-9a-f]{64})$ ]]; then
            version="${BASH_REMATCH[1]}"
            digest="${BASH_REMATCH[2]}"
            count=$((count + 1))
        else
            die "$NODE_IMAGE_FILE has a line that is not '<version> sha256:<64-hex>': $line"
        fi
    done <"$NODE_IMAGE_FILE"
    [[ "$count" -eq 1 ]] || die "$NODE_IMAGE_FILE must contain exactly one digest line"
    RECORD_VERSION="$version"
    RECORD_DIGEST="$digest"
}

consumers_match() {
    local digest="$1" file got
    got="$(dockerfile_digest)" || return 1
    [[ "$got" == "$digest" ]] || return 1
    for file in "${ENGINE_FILES[@]}"; do
        got="$(first_node_engine "$file")" || return 1
        [[ "$got" == ">=$NODE_VERSION" ]] || return 1
    done
    for file in "${DOC_FILES[@]}"; do
        got="$(first_node_semver "$file")" || return 1
        [[ "$got" == "$NODE_VERSION" ]] || return 1
        doc_has_marker "$file" || return 1
    done
}

fetch_manifest_list_digest() {
    local version="$1" token headers content_type digest
    token="$(
        curl -fsSL "https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/node:pull" |
            sed -n 's/.*"token"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p'
    )"
    [[ -n "$token" ]] || die "Docker Hub token response had no token"
    headers="$(
        curl -fsSLI \
            -H "Authorization: Bearer ${token}" \
            -H "Accept: application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.index.v1+json" \
            "https://registry-1.docker.io/v2/library/node/manifests/${version}-alpine" | tr -d '\r'
    )"
    # The registry may answer with a single-platform manifest even when the
    # Accept header asks for a list, and -L can leave several response
    # headers in the output. Read the last of each, and refuse anything but
    # a manifest list or an OCI index: a single-platform digest would break
    # a multi-arch build.
    content_type="$(awk 'tolower($1) == "content-type:" { v = tolower($2) } END { print v }' <<<"$headers")"
    case "$content_type" in
        application/vnd.docker.distribution.manifest.list.v2+json* | application/vnd.oci.image.index.v1+json*) ;;
        *) die "expected a manifest list or OCI index for node:${version}-alpine, got content-type: ${content_type:-<empty>}" ;;
    esac
    digest="$(awk 'tolower($1) == "docker-content-digest:" { v = $2 } END { print v }' <<<"$headers")"
    [[ "$digest" =~ ^sha256:[0-9a-f]{64}$ ]] || die "no manifest-list digest for node:${version}-alpine"
    printf '%s' "$digest"
}

rewrite_engines() {
    local file="$1" tmp="$TMP_DIR/out"
    awk -v ver="$NODE_VERSION" '
        BEGIN { done = 0; in_deps = 0 }
        index($0, "\"node_modules/") > 0 { in_deps = 1 }
        done == 0 && !in_deps && $0 ~ /"node":[[:space:]]*">=[0-9]+\.[0-9]+\.[0-9]+"/ {
            sub(/>=[0-9]+\.[0-9]+\.[0-9]+/, ">=" ver)
            done = 1
        }
        { print }
        END { if (done == 0) exit 2 }
    ' "$file" >"$tmp" || die "$file has no root engines.node floor to rewrite"
    cat "$tmp" >"$file"
}

# The install sentence is the first line with Node.js, a semver, and
# " or higher" (the same line first_node_semver reads). Without one the
# script stops before writing anything.
rewrite_doc() {
    local file="$1" tmp="$TMP_DIR/out"
    awk -v ver="$NODE_VERSION" -v marker="$MARKER" '
        BEGIN { done = 0 }
        done == 0 && index($0, "Node.js") > 0 && index($0, " or higher") > 0 && match($0, /[0-9]+\.[0-9]+\.[0-9]+/) {
            $0 = substr($0, 1, RSTART - 1) ver substr($0, RSTART + RLENGTH)
            if (index($0, marker) == 0) {
                sub(/ or higher/, " " marker " or higher")
            }
            done = 1
        }
        { print }
        END { if (done == 0) exit 2 }
    ' "$file" >"$tmp" || die "$file has no Node.js install sentence (Node.js, a version, and 'or higher') to rewrite"
    cat "$tmp" >"$file"
}

rewrite_dockerfile_digest() {
    local digest="$1" tmp="$TMP_DIR/out"
    awk -v digest="$digest" '
        BEGIN { done = 0 }
        /^FROM / && index($0, "node:") > 0 {
            if (sub(/@sha256:[0-9a-f]+/, "@" digest)) {
                done = 1
            }
        }
        { print }
        END { if (done == 0) exit 2 }
    ' "$DOCKERFILE" >"$tmp" || die "$DOCKERFILE has no digest-pinned FROM node line"
    cat "$tmp" >"$DOCKERFILE"
}

write_record() {
    local digest="$1"
    mkdir -p "$(dirname "$NODE_IMAGE_FILE")"
    cat >"$NODE_IMAGE_FILE" <<EOF
# Manifest-list digest of node:<version>-alpine. Regenerated by task tools:sync-node.
${NODE_VERSION} ${digest}
EOF
}

read_record

if [[ "${RECORD_VERSION:-}" == "$NODE_VERSION" && -n "${RECORD_DIGEST:-}" ]] && consumers_match "$RECORD_DIGEST"; then
    echo "node consumers already match $NODE_VERSION" >&2
    exit 0
fi

if [[ -n "${NODE_IMAGE_DIGEST:-}" ]]; then
    DIGEST="$NODE_IMAGE_DIGEST"
elif [[ "${RECORD_VERSION:-}" == "$NODE_VERSION" && -n "${RECORD_DIGEST:-}" ]]; then
    DIGEST="$RECORD_DIGEST"
else
    DIGEST="$(fetch_manifest_list_digest "$NODE_VERSION")"
fi

[[ "$DIGEST" =~ ^sha256:[0-9a-f]{64}$ ]] || die "digest must look like sha256:<64-hex>, got: $DIGEST"

write_record "$DIGEST"
rewrite_dockerfile_digest "$DIGEST"
for file in "${ENGINE_FILES[@]}"; do
    rewrite_engines "$file"
done
for file in "${DOC_FILES[@]}"; do
    rewrite_doc "$file"
done

echo "updated node consumers to $NODE_VERSION ($DIGEST)" >&2
