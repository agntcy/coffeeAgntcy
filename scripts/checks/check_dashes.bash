#!/usr/bin/env bash
# Checks the whole repo for en dash (U+2013) or em dash (U+2014) - see
# .agents/rules/no-em-en-dashes.md. Thin wrapper pinning the patterns this
# repo forbids, so the dashes:check task, task check:all, and CI all check
# the exact same two characters.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec "$SCRIPT_DIR/check_forbidden_strings.bash" \
    --pattern $'\u2013' \
    --pattern $'\u2014' \
    --error-message "Forbidden string found (en dash or em dash - use a plain hyphen)."
