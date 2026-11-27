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
# The dir-mcp release assets are additionally signature-verified: the
# upstream project publishes only a sigstore bundle next to each binary, no
# checksum file, so a bare download would pin whatever the network served.
# Each asset's "<url>.sigstore.json" bundle is checked with sigstore against
# the release workflow's signer identity, and a hash is recorded only if that
# succeeds. Nothing is written to the output file unless every asset
# verified.
#
# The verifier itself is hash-pinned: before anything is downloaded, sigstore
# and all its dependencies are installed into a throwaway venv from
# scripts/lib/sigstore/requirements.txt with `uv pip install
# --require-hashes --no-deps --no-build`, ignoring any uv config file. The
# venv needs Python >=3.10 (what sigstore requires) and is created with
# --no-python-downloads, so a machine without a suitable interpreter fails
# loudly instead of uv fetching an unpinned one. The script refuses to run
# when that file pins a different sigstore than SIGSTORE_VERSION (regenerate
# it with `task tools:sigstore-lock`).
#
# uv is resolved like in update_sigstore_lock.bash: UV_BIN, then the
# repo-local .tools/bin/uv, then PATH.
#
# CHECKSUMS_FILE (default scripts/lib/checksums.txt),
# SIGSTORE_REQUIREMENTS_FILE (default scripts/lib/sigstore/requirements.txt)
# and UV_BIN are overridable so the test can use fixtures instead of the real files.
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
: "${SIGSTORE_REQUIREMENTS_FILE:=$REPO_ROOT/scripts/lib/sigstore/requirements.txt}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# Prepare the hash-pinned verifier only when dir-mcp is going to be verified.
SIGSTORE_BIN=""
for tool in "${ASSET_TOOLS[@]}"; do
    if [[ "$tool" == "dir-mcp" ]]; then
        if [[ ! -f "$SIGSTORE_REQUIREMENTS_FILE" ]]; then
            echo "error: $SIGSTORE_REQUIREMENTS_FILE not found; run 'task tools:sigstore-lock'" >&2
            exit 1
        fi
        locked_version="$(awk '/^sigstore==/ { sub(/^sigstore==/, ""); print $1; exit }' "$SIGSTORE_REQUIREMENTS_FILE")"
        if [[ "$locked_version" != "$SIGSTORE_VERSION" ]]; then
            echo "error: $SIGSTORE_REQUIREMENTS_FILE pins sigstore ${locked_version:-<none>} but versions.sh pins $SIGSTORE_VERSION; run 'task tools:sigstore-lock'" >&2
            exit 1
        fi
        if [[ -z "${UV_BIN:-}" ]]; then
            UV_BIN="$REPO_ROOT/.tools/bin/uv"
            if [[ ! -x "$UV_BIN" ]]; then
                UV_BIN="$(command -v uv || true)"
            fi
        fi
        if [[ -z "$UV_BIN" ]]; then
            echo "error: uv not found. Run ./scripts/setup.sh and 'source scripts/env.sh' first." >&2
            exit 2
        fi
        # --no-config: a user or system uv.toml must not steer the install;
        # --no-build: a missing wheel fails instead of fetching build backends
        # that the lock's hashes do not cover; --no-python-downloads: only an
        # interpreter already on the machine is used.
        "$UV_BIN" --no-config venv --python '>=3.10' --no-python-downloads "$TMP_DIR/sigstore-venv" >&2
        "$UV_BIN" --no-config pip install --python "$TMP_DIR/sigstore-venv/bin/python" \
            --require-hashes --no-deps --no-build \
            -r "$SIGSTORE_REQUIREMENTS_FILE" >&2
        SIGSTORE_BIN="$TMP_DIR/sigstore-venv/bin/sigstore"
    fi
done

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
        if [[ "$tool" == "dir-mcp" ]]; then
            echo "verifying $url" >&2
            FETCH "$url.sigstore.json" >"$TMP_DIR/asset.sigstore.json"
            if ! "$SIGSTORE_BIN" verify identity \
                --bundle "$TMP_DIR/asset.sigstore.json" \
                --cert-identity "https://github.com/agntcy/dir-mcp/.github/workflows/release.yml@refs/tags/v${DIR_MCP_VERSION}" \
                --cert-oidc-issuer https://token.actions.githubusercontent.com \
                "$TMP_DIR/asset" >&2; then
                echo "error: sigstore verification failed for $url" >&2
                exit 1
            fi
        fi
        echo "$(sha256_of "$TMP_DIR/asset")  $url" >>"$TMP_DIR/lines"
    done
done

LC_ALL=C sort -k2 "$TMP_DIR/lines" >"$CHECKSUMS_FILE"
echo "wrote ${#seen[@]} checksums to $CHECKSUMS_FILE" >&2
