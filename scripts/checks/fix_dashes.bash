#!/usr/bin/env bash
# Replaces every en dash (U+2013) or em dash (U+2014) in the repo with a
# plain ASCII hyphen - see .agents/rules/no-em-en-dashes.md.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$SCRIPT_DIR/find_strings.bash" \
    --pattern $'\u2013' \
    --pattern $'\u2014' \
    --replace-with '-' \
    --write
rc=$?

# find_strings.bash exits 1 when nothing matched - a clean repo, not a
# failure for a fix command.
if [[ "$rc" -eq 1 ]]; then
    echo "No en dash or em dash found - nothing to fix."
    exit 0
fi
exit "$rc"
