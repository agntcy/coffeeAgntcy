#!/usr/bin/env bash
# Renovate postUpgradeTask: auto-fix lint/format drift in every frontend
# after a dependency update (see the Frontend packageRule in renovate.json).
#
# For each */frontend/package.json it installs the lockfile's dependencies
# without running install scripts, then runs the project's `lint` script
# (`eslint . --fix`). Renovate then commits whatever changed under the
# rule's fileFilters. A lint run that still reports unfixable problems is
# not an error here: the PR is still created and CI shows what is left.
#
# Runs from the repo root, which is where Renovate executes the command;
# the only command allowed to run is this script, via
# RENOVATE_ALLOWED_COMMANDS in .github/workflows/renovate.yaml.
#
# Usage: scripts/renovate/fix_frontend_lint.bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

while IFS= read -r package_json; do
    dir="$(dirname "$package_json")"
    echo "==> $dir"
    (
        cd "$dir"
        npm ci --ignore-scripts --no-audit --no-fund
        npm run lint || echo "warning: lint reported problems it could not fix in $dir" >&2
    )
done < <(find . -path '*/frontend/package.json' -not -path '*/node_modules/*' | sort)
