#!/usr/bin/env bash
# Prints every tool version pinned in scripts/lib/versions.sh (the single
# source of truth, see .agents/rules/meta/pinned-tool-versions.md) as a
# "<tool>  <version>  <sha256>" table, alphabetical, with any leading "v"
# stripped from the version. Variable names are read from the file itself,
# so unrelated *_VERSION variables in the caller's environment never leak in.
#
# The third column is the pinned SHA-256 of what setup.sh installs for this
# machine: the tool's archive for this OS/arch from scripts/lib/checksums.txt,
# or, for the npm tools (openspec, renovate), the package's integrity hash
# (sha512, base64) from scripts/lib/npm-tools/package-lock.json. "-" when a
# tool has no pinned hash.
#
# VERSIONS_FILE (default scripts/lib/versions.sh) is overridable so the
# test can point it at a fixture.
#
# Usage: scripts/tools/print_versions.bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

: "${VERSIONS_FILE:=$REPO_ROOT/scripts/lib/versions.sh}"
# shellcheck source=scripts/lib/versions.sh
source "$VERSIONS_FILE"
# shellcheck source=scripts/lib/assets.sh
source "$REPO_ROOT/scripts/lib/assets.sh"
# shellcheck source=scripts/lib/platform.sh
source "$REPO_ROOT/scripts/lib/platform.sh"

OS="$(detect_os)"
ARCH="$(detect_arch_gnu)"
CHECKSUMS_FILE="$REPO_ROOT/scripts/lib/checksums.txt"
LOCK_FILE="$REPO_ROOT/scripts/lib/npm-tools/package-lock.json"

# hash_of <tool>: the pinned hash for this machine, or "-".
hash_of() {
    local tool="$1" url hash="" pkg
    case "$tool" in
        openspec) pkg="@fission-ai/openspec" ;;
        renovate) pkg="renovate" ;;
        *) pkg="" ;;
    esac
    if [[ -n "$pkg" ]]; then
        hash="$(awk -v key="\"node_modules/$pkg\": {" '
            index($0, key) {found = 1}
            found && /"integrity":/ {gsub(/[",]/, "", $2); print $2; exit}' "$LOCK_FILE" 2>/dev/null || true)"
    elif url="$(asset_url "$tool" "$OS" "$ARCH" 2>/dev/null)"; then
        hash="$(awk -v u="$url" '$2 == u {print $1; exit}' "$CHECKSUMS_FILE" 2>/dev/null || true)"
    fi
    echo "${hash:--}"
}

while IFS= read -r var; do
    value="${!var}"
    tool="$(tr '[:upper:]' '[:lower:]' <<<"${var%_VERSION}")"
    printf '%s %s %s\n' "$tool" "${value#v}" "$(hash_of "$tool")"
done < <(sed -n 's/^\([A-Z_]*_VERSION\)=.*/\1/p' "$VERSIONS_FILE" | LC_ALL=C sort) | column -t
