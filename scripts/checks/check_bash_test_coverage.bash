#!/usr/bin/env bash
# Audits .agents/rules/quality/bash-script-testing.md's requirement that
# every bash script in this repository has a test: for each *.bash/*.sh
# file anywhere in the repo (excluding the tests/ directories themselves,
# and the usual vendored/tooling directories), confirms a corresponding
# tests/<name>.bats file exists.
#
# A script's expected test lives at <its-own-dir>/tests/<basename
# without .bash/.sh>.bats - e.g. scripts/checks/check_dashes.bash's test
# is scripts/checks/tests/check_dashes.bats, and scripts/setup.sh's is
# scripts/tests/setup.bats.
#
# No exceptions list: every bash script added to this repository from
# now on needs a test in the same change that adds it, full stop - there
# used to be a grandfathered "not yet tested" allow-list here for the
# scripts that predated this rule, removed once the backfill gave every
# one of them a real test.
#
# SCAN_DIR (default ".", i.e. the whole repo) is overridable so this
# script's own test can point it at a fixture tree instead of scanning
# the real repo.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT" || exit 2

: "${SCAN_DIR:=.}"

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

    echo "error: $script has no test ($expected_test not found) - add one in the same change."
    failed=1
done

if [[ "$failed" -eq 0 ]]; then
    echo "OK: every script under $SCAN_DIR ($checked checked) has a test."
fi

exit "$failed"
