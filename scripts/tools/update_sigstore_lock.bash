#!/usr/bin/env bash
# Regenerates scripts/lib/sigstore/requirements.txt for the SIGSTORE_VERSION
# pinned in scripts/lib/versions.sh: a universal requirements file in which
# sigstore and every transitive package is pinned by SHA-256, so the verifier
# that scripts/tools/update_checksums.bash runs is itself hash-pinned (it
# installs the file with `uv pip install --require-hashes`).
#
# The file is compiled for Python 3.10, the lowest version the pinned
# sigstore release supports (its requires-python is >=3.10), with
# --universal so one file resolves on every platform and every newer Python,
# and --no-header so the file does not record the temp paths of the run.
# --exclude-newer "14 days" keeps every package, transitive ones included,
# at a release at least two weeks old (the repo's age gate), and
# --no-config stops a user or system uv.toml from steering the resolution.
#
# Run after bumping SIGSTORE_VERSION (see the manage-repo-tooling skill);
# update_checksums.bash refuses to run while the file's sigstore pin differs
# from SIGSTORE_VERSION. Review the resulting diff.
#
# Prefers the repo-local uv installed by scripts/setup.sh, falling back to
# whatever is on PATH.
#
# LOCK_DIR (default scripts/lib/sigstore) and UV_BIN are overridable so the
# test can write to a fixture with a mocked uv instead of touching the real
# file.
#
# Usage: scripts/tools/update_sigstore_lock.bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=scripts/lib/versions.sh
source "$REPO_ROOT/scripts/lib/versions.sh"

: "${LOCK_DIR:=$REPO_ROOT/scripts/lib/sigstore}"

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

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "sigstore==$SIGSTORE_VERSION" >"$TMP_DIR/requirements.in"

# Run from inside the temp dir with relative paths: uv records the input path
# in the file's "# via -r <input>" annotations, which must not be a temp path.
(cd "$TMP_DIR" && "$UV_BIN" --no-config pip compile requirements.in --universal --generate-hashes \
    --no-header --exclude-newer "14 days" --python-version 3.10 -o requirements.txt) >&2

mkdir -p "$LOCK_DIR"
cp "$TMP_DIR/requirements.txt" "$LOCK_DIR/requirements.txt"
echo "wrote $LOCK_DIR/requirements.txt" >&2
