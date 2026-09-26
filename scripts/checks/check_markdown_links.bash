#!/usr/bin/env bash
# Ensures every relative markdown link (`[text](target)`) in every
# git-tracked *.md file actually resolves to a file that exists - a
# `.md` file's own commit doesn't move together with the files it
# links to, so a rename/move elsewhere in the repo silently leaves a
# dangling reference behind unless something re-checks every link.
#
# A target is skipped, not checked, when it:
#   - is an http(s)/mailto link, or a bare in-page `#anchor`
#   - is a GitHub web path (e.g. `/<owner>/<repo>/blob/<ref>/...`) rather
#     than a path into this repo's own working tree
#   - contains a `<...>` placeholder segment (e.g. `path/<rule>.md`),
#     since that's prose illustrating a naming pattern, not a real link
#   - is on a line carrying a trailing `<!-- link-exempt: <reason> -->`
#     comment, as long as it states a reason (same opt-out shape as
#     check_pinned_references.bash's `# pin-exempt:`)
#
# A target starting with `/` resolves from the repo root (as GitHub
# renders it); anything else resolves relative to the linking file's own
# directory. A trailing `#anchor` is stripped before the existence check
# - this only verifies the target file exists, not that the anchor is a
# real heading in it.
#
# Covers only inline links - reference-style links (`[text][ref]` with a
# separate `[ref]: target` definition elsewhere) aren't scanned, since
# this repo doesn't use that style anywhere today. Extend this script if
# that changes rather than leaving it a silent gap.
#
# See .agents/rules/quality/markdown-link-integrity.md.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT" || exit 2

failed=0
checked=0

mapfile -t md_files < <(git ls-files -- "*.md")

for file in "${md_files[@]}"; do
    mapfile -t lines <"$file"
    line_num=0
    for line in "${lines[@]}"; do
        line_num=$((line_num + 1))

        exempt_reason=""
        exempt_pattern='link-exempt:[[:space:]]*(.*)--'
        exempt_pattern+='>'
        if [[ "$line" == *"link-exempt:"* ]] && [[ "$line" =~ $exempt_pattern ]]; then
            exempt_reason="${BASH_REMATCH[1]}"
            if [[ -z "${exempt_reason// /}" ]]; then
                echo "$file:$line_num: 'link-exempt' comment must state a reason, e.g. '<!-- link-exempt: why this cannot resolve -->'"
                failed=1
            fi
        fi

        remaining="$line"
        while [[ "$remaining" =~ \]\(([^\)]+)\) ]]; do
            target="${BASH_REMATCH[1]}"
            remaining="${remaining#*"${BASH_REMATCH[0]}"}"

            case "$target" in
                http://* | https://* | mailto:* | \#*) continue ;;
                /*/*/blob/* | /*/*/tree/* | /*/*/raw/*) continue ;;
                *"<"*) continue ;;
            esac

            [[ -n "$exempt_reason" ]] && continue

            target_path="${target%%#*}"
            [[ -z "$target_path" ]] && continue

            if [[ "$target_path" == /* ]]; then
                resolved="$REPO_ROOT${target_path}"
            else
                resolved="$(dirname "$file")/$target_path"
            fi

            checked=$((checked + 1))
            if [[ ! -e "$resolved" ]]; then
                echo "$file:$line_num: '$target' does not resolve to an existing file (resolved: $resolved)"
                failed=1
            fi
        done
    done
done

if [[ "$failed" -ne 0 ]]; then
    exit 1
fi
echo "OK: every relative link in $checked checked reference(s) across ${#md_files[@]} markdown file(s) resolves."
