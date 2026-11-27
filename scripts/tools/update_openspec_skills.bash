#!/usr/bin/env bash
# Regenerates the OpenSpec skills (.agents/skills/openspec-*/SKILL.md) so
# every generatedBy stamp equals OPENSPEC_VERSION in scripts/lib/versions.sh.
#
# Installs the pinned openspec from the committed lockfile
# (scripts/lib/npm-tools/package-lock.json) into a temp dir with
# `npm ci --ignore-scripts`, then runs `openspec update` on the repo. It
# never uses a bare registry version, and never touches .tools/. Exits 0
# without network when every stamp already matches.
#
# Run after bumping OPENSPEC_VERSION and refreshing the lockfile
# (task tools:npm-lock). Renovate runs it itself as a post-upgrade task,
# after update_npm_lock.bash. Review the skill diff.
#
# Prefers the repo-local npm installed by scripts/setup.sh, falling back
# to whatever is on PATH.
#
# REPO_ROOT (default: the repo that contains this script), NPM_BIN and
# OPENSPEC_BIN are overridable for the test. When OPENSPEC_BIN is set the
# install step is skipped and that binary runs instead.
#
# Usage: scripts/tools/update_openspec_skills.bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "${REPO_ROOT:-}" ]]; then
    REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

# shellcheck source=scripts/lib/versions.sh
source "$REPO_ROOT/scripts/lib/versions.sh"
# shellcheck source=scripts/lib/npm_tools.sh
source "$REPO_ROOT/scripts/lib/npm_tools.sh"

SKILLS_DIR="$REPO_ROOT/.agents/skills"
LOCK_FILE="$REPO_ROOT/scripts/lib/npm-tools/package-lock.json"

die() {
    echo "error: $*" >&2
    exit 1
}

# Prints each skill file whose generatedBy stamp is missing or not the pin.
stale_skills() {
    local file line stamp
    [[ -d "$SKILLS_DIR" ]] || return 0
    while IFS= read -r file; do
        [[ -n "$file" ]] || continue
        stamp=""
        while IFS= read -r line || [[ -n "$line" ]]; do
            if [[ "$line" =~ generatedBy:[[:space:]]*[\"\']?([^\"\'[:space:]]+) ]]; then
                stamp="${BASH_REMATCH[1]}"
                break
            fi
        done <"$file"
        if [[ "$stamp" != "$OPENSPEC_VERSION" ]]; then
            printf '%s\n' "$file"
        fi
    done < <(find "$SKILLS_DIR" -type f -path '*/openspec-*/SKILL.md' | sort)
}

if [[ ! -d "$SKILLS_DIR" ]] || [[ -z "$(find "$SKILLS_DIR" -type f -path '*/openspec-*/SKILL.md')" ]]; then
    echo "no OpenSpec skills under $SKILLS_DIR, nothing to update" >&2
    exit 0
fi
if [[ -z "$(stale_skills)" ]]; then
    echo "openspec skills already match $OPENSPEC_VERSION" >&2
    exit 0
fi

if [[ -z "${OPENSPEC_BIN:-}" ]]; then
    if [[ -z "${NPM_BIN:-}" ]]; then
        NPM_BIN="$REPO_ROOT/.tools/node/bin/npm"
        if [[ ! -x "$NPM_BIN" ]]; then
            NPM_BIN="$(command -v npm || true)"
        fi
    fi
    [[ -n "$NPM_BIN" ]] || die "npm not found. Run ./scripts/setup.sh and 'source scripts/env.sh' first."
    [[ -f "$LOCK_FILE" ]] || die "$LOCK_FILE is missing. Run task tools:npm-lock first."

    TMP_DIR="$(mktemp -d)"
    trap 'rm -rf "$TMP_DIR"' EXIT

    write_npm_tools_package_json "$TMP_DIR"
    cp "$LOCK_FILE" "$TMP_DIR/package-lock.json"
    # Node has to be on PATH: the openspec shim starts with
    # `#!/usr/bin/env node`.
    PATH="$(dirname "$NPM_BIN"):$PATH"
    (cd "$TMP_DIR" && "$NPM_BIN" ci --ignore-scripts --no-audit --no-fund \
        --userconfig=/dev/null --cache="$TMP_DIR/.npm-cache") >&2
    OPENSPEC_BIN="$TMP_DIR/node_modules/.bin/openspec"
fi

installed="$("$OPENSPEC_BIN" --version)"
[[ "$installed" == "$OPENSPEC_VERSION" ]] ||
    die "openspec is $installed, OPENSPEC_VERSION is $OPENSPEC_VERSION. Refresh the lockfile with task tools:npm-lock."

(cd "$REPO_ROOT" && "$OPENSPEC_BIN" update) >&2

remaining="$(stale_skills)"
if [[ -n "$remaining" ]]; then
    die "openspec update left these skills without a $OPENSPEC_VERSION stamp: $remaining"
fi
echo "openspec skills now match $OPENSPEC_VERSION" >&2
