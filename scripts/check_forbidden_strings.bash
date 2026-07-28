#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIND_STRINGS="${SCRIPT_DIR}/find_strings.bash"

usage() {
	cat <<'EOF'
Usage:
  check_forbidden_strings.bash \
    --pattern STRING [--pattern STRING ...] \
    [--search-path PATH] \
    [--exclude-dir DIR ...] \
    [--exclude-glob GLOB ...] \
    [--error-message MSG]

Checks the repository for forbidden substrings.
Emits GitHub workflow error annotations on stdout.

Exit codes:
  0 = no forbidden strings found
  1 = one or more forbidden strings found
  2 = invalid args
EOF
}

search_path="."
patterns=()
exclude_dirs=()
exclude_globs=()
error_message="Forbidden string(s) found in repository"

while [[ $# -gt 0 ]]; do
	case "$1" in
	--pattern)
		patterns+=("$2")
		shift 2
		;;
	--search-path)
		search_path="$2"
		shift 2
		;;
	--exclude-dir)
		exclude_dirs+=("$2")
		shift 2
		;;
	--exclude-glob)
		exclude_globs+=("$2")
		shift 2
		;;
	--error-message)
		error_message="$2"
		shift 2
		;;
	-h | --help)
		usage
		exit 0
		;;
	*)
		echo "unknown argument: $1" >&2
		usage >&2
		exit 2
		;;
	esac
done

if ((${#patterns[@]} == 0)); then
	echo "at least one --pattern is required" >&2
	exit 2
fi

describe_needle() {
	case "$(printf '%s' "$1" | od -An -tx1 | tr -d ' \n')" in
	c2*) printf '%s' "$1" ;;
	*) printf '%q' "$1" ;;
	esac
}

args=(--search-path "$search_path")
for dir in "${exclude_dirs[@]}"; do args+=(--exclude-dir "$dir"); done
for glob in "${exclude_globs[@]}"; do args+=(--exclude-glob "$glob"); done
for pattern in "${patterns[@]}"; do args+=(--pattern "$pattern"); done

# find_strings: exit 0 = matches, 1 = clean
if ! hits="$("$FIND_STRINGS" "${args[@]}")"; then
	[[ -n "${GITHUB_OUTPUT:-}" ]] && echo "found=false" >>"$GITHUB_OUTPUT"
	exit 0
fi

found=false
while IFS=$'\t' read -r file line pattern content; do
	[[ -z "$file" ]] && continue
	found=true
	needle_desc="$(describe_needle "$pattern")"
	echo "::error file=${file},line=${line},title=${error_message}::Forbidden string '${needle_desc}' at ${file}:${line}: ${content}"
done <<<"$hits"

if [[ "$found" == true ]]; then
	[[ -n "${GITHUB_OUTPUT:-}" ]] && echo "found=true" >>"$GITHUB_OUTPUT"
	exit 1
fi

exit 0
