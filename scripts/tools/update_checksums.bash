#!/usr/bin/env bash
# Regenerates scripts/lib/checksums.txt: downloads every tool archive
# scripts/setup.sh can fetch (see scripts/lib/assets.sh) for every
# supported platform at the versions pinned in scripts/lib/versions.sh, and
# records each one's SHA-256 as "<sha256>  <url>" lines, sorted by URL.
#
# Run after bumping or adding a pin in scripts/lib/versions.sh (see the
# manage-repo-tooling skill); scripts/setup.sh refuses to install any
# archive whose URL has no matching line. Review the resulting diff: the
# hashes are only as trustworthy as the network path this script ran over,
# so cross-check them against the upstream project's published checksums
# where it has any.
#
# CHECKSUMS_FILE (default scripts/lib/checksums.txt) is overridable so the
# test can write to a fixture instead of the real file.
#
# Usage: scripts/tools/update_checksums.bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=scripts/lib/versions.sh
source "$REPO_ROOT/scripts/lib/versions.sh"
# shellcheck source=scripts/lib/fetch.sh
source "$REPO_ROOT/scripts/lib/fetch.sh"
# shellcheck source=scripts/lib/assets.sh
source "$REPO_ROOT/scripts/lib/assets.sh"

ensure_fetcher

: "${CHECKSUMS_FILE:=$REPO_ROOT/scripts/lib/checksums.txt}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

declare -A seen=()
: >"$TMP_DIR/lines"
for tool in "${ASSET_TOOLS[@]}"; do
    for platform in "${SUPPORTED_PLATFORMS[@]}"; do
        url="$(asset_url "$tool" "${platform%-*}" "${platform#*-}")"
        # Some assets (bats source tarball) are platform-independent.
        [[ -n "${seen[$url]:-}" ]] && continue
        seen[$url]=1
        echo "fetching $url" >&2
        FETCH "$url" >"$TMP_DIR/asset"
        echo "$(sha256_of "$TMP_DIR/asset")  $url" >>"$TMP_DIR/lines"
    done
done

LC_ALL=C sort -k2 "$TMP_DIR/lines" >"$CHECKSUMS_FILE"
echo "wrote ${#seen[@]} checksums to $CHECKSUMS_FILE" >&2
