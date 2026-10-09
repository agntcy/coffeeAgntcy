#!/usr/bin/env bash
# Regenerates scripts/lib/npm-tools/package-lock.json for the OPENSPEC_VERSION
# and RENOVATE_VERSION pinned in scripts/lib/versions.sh: generates the same
# package.json setup.sh uses (scripts/lib/npm_tools.sh), starts from the
# committed lockfile so transitive packages only move where the new pins
# require it, and writes the result back. Never runs package install scripts.
#
# Run after bumping either version (see the manage-repo-tooling skill);
# Renovate runs it itself as a post-upgrade task. Review the lockfile diff.
#
# Prefers the repo-local npm installed by scripts/setup.sh, falling back to
# whatever is on PATH.
#
# LOCK_DIR (default scripts/lib/npm-tools) and NPM_BIN are overridable so
# the test can write to a fixture with a mocked npm instead of touching the
# real lockfile.
#
# Usage: scripts/tools/update_npm_lock.bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=scripts/lib/versions.sh
source "$REPO_ROOT/scripts/lib/versions.sh"
# shellcheck source=scripts/lib/npm_tools.sh
source "$REPO_ROOT/scripts/lib/npm_tools.sh"

: "${LOCK_DIR:=$REPO_ROOT/scripts/lib/npm-tools}"

if [[ -z "${NPM_BIN:-}" ]]; then
    NPM_BIN="$REPO_ROOT/.tools/node/bin/npm"
    if [[ ! -x "$NPM_BIN" ]]; then
        NPM_BIN="$(command -v npm || true)"
    fi
fi
if [[ -z "$NPM_BIN" ]]; then
    echo "error: npm not found. Run ./scripts/setup.sh and 'source scripts/env.sh' first." >&2
    exit 2
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

write_npm_tools_package_json "$TMP_DIR"
if [[ -f "$LOCK_DIR/package-lock.json" ]]; then
    cp "$LOCK_DIR/package-lock.json" "$TMP_DIR/package-lock.json"
fi

# Run from inside the temp dir rather than via --prefix: npm then treats it
# as the project root (with --prefix it recorded the temp path in the lock).
(cd "$TMP_DIR" && "$NPM_BIN" install --package-lock-only --ignore-scripts --no-audit --no-fund \
    --userconfig=/dev/null --cache="$TMP_DIR/.npm-cache") >&2

mkdir -p "$LOCK_DIR"
cp "$TMP_DIR/package-lock.json" "$LOCK_DIR/package-lock.json"
echo "wrote $LOCK_DIR/package-lock.json" >&2
