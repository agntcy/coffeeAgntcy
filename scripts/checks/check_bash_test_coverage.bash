#!/usr/bin/env bash
# Audits .agents/rules/quality/bash-script-testing.md's requirement that
# every bash script in this repository has a test: for each *.bash/*.sh
# file anywhere in the repo (excluding the tests/ directories
# themselves, and the usual vendored/tooling directories), confirms a
# corresponding tests/<name>.bats file exists, unless that script's path
# is listed below as predating the rule.
#
# A script's expected test lives at <its-own-dir>/tests/<basename
# without .bash/.sh>.bats - e.g. scripts/checks/check_dashes.bash's test
# is scripts/checks/tests/check_dashes.bats, and scripts/setup.sh's is
# scripts/tests/setup.bats.
#
# NOT_YET_TESTED is the deferred backfill's own punch list: every script
# that existed before this rule was introduced. It shrinks one line at a
# time as each script gets a test - promote a script out of this list in
# the same change that adds its test file, don't leave it listed once it
# has one (the audit doesn't require that, but a stale entry here is the
# same kind of lie repo-operation-pipeline.md's own exceptions list
# would be if left unpromoted).
#
# SCAN_DIR (default ".", i.e. the whole repo) and NOT_YET_TESTED_EXTRA
# (default empty, a space-separated list of extra grandfathered paths)
# are overridable so this script's own test can point it at a fixture
# tree with its own fixture-specific grandfather list, instead of
# scanning the real repo against the real one below.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT" || exit 2

: "${SCAN_DIR:=.}"
: "${NOT_YET_TESTED_EXTRA:=}"

NOT_YET_TESTED=()

is_grandfathered() {
    local script="$1" entry
    # "${NOT_YET_TESTED[@]:-}" (not a bare "${NOT_YET_TESTED[@]}") because
    # this array is legitimately empty right now (everything's tested) -
    # macOS's system /bin/bash (still 3.2) treats expanding an empty
    # array under `set -u` as an unbound-variable error, unlike every
    # bash >=4.4. The ":-" fallback yields one harmless empty-string
    # entry instead, which never matches a real script path below.
    for entry in "${NOT_YET_TESTED[@]:-}" $NOT_YET_TESTED_EXTRA; do
        [[ "$entry" == "$script" ]] && return 0
    done
    return 1
}

failed=0
checked=0

mapfile -t found_scripts < <(find "$SCAN_DIR" \
    \( -path "*/node_modules" -o -path "*/.venv" -o -path "*/.git" -o -path "*/.tools" \) -prune -o \
    -type f \( -name "*.bash" -o -name "*.sh" \) -not -path "*/tests/*" -print | sort)

for raw_script in "${found_scripts[@]}"; do
    script="${raw_script#./}"
    checked=$((checked + 1))
    dir="$(dirname "$script")"
    base="$(basename "$script")"
    expected_test="$dir/tests/${base%.*}.bats"

    if [[ -f "$expected_test" ]]; then
        continue
    fi

    if is_grandfathered "$script"; then
        continue
    fi

    echo "error: $script has no test ($expected_test not found) and is not in this script's NOT_YET_TESTED list - add a test, or add it to the list if this is itself a pre-existing script the backfill hasn't reached yet."
    failed=1
done

if [[ "$failed" -eq 0 ]]; then
    echo "OK: every non-grandfathered script under $SCAN_DIR ($checked checked) has a test."
fi

exit "$failed"
