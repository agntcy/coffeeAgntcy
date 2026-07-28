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

Expects find_strings.bash TSV columns:
  file  line  pattern (U+XXXX)  content

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

describe_needle_from_field() {
	local pattern_field="$1"
	local visual code

	# find_strings emits: "— (U+2014)" or "foo (U+0066,U+006F,U+006F)"
	if [[ "$pattern_field" =~ ^(.*)[[:space:]]+\((U\+[0-9A-F]+(,[U\+[0-9A-F]+)*)\)$ ]]; then
		visual="${BASH_REMATCH[1]}"
		code="${BASH_REMATCH[2]}"
		printf '%s (%s)' "$visual" "$code"
		return 0
	fi

	printf '%s' "$pattern_field"
}

args=(--search-path "$search_path")
for dir in "${exclude_dirs[@]}"; do args+=(--exclude-dir "$dir"); done
for glob in "${exclude_globs[@]}"; do args+=(--exclude-glob "$glob"); done
for pattern in "${patterns[@]}"; do args+=(--pattern "$pattern"); done

found=false
hit_count=0

while IFS=$'\t' read -r file line pattern_field content; do
	[[ -z "$file" ]] && continue
	found=true
	hit_count=$((hit_count + 1))
	needle_desc="$(describe_needle_from_field "$pattern_field")"
	echo "::error file=${file},line=${line},title=${error_message}::Forbidden string ${needle_desc} at ${file}:${line}: ${content}"
done < <("$FIND_STRINGS" "${args[@]}")

if [[ "$found" != true ]]; then
	[[ -n "${GITHUB_OUTPUT:-}" ]] && {
		echo "found=false" >>"$GITHUB_OUTPUT"
		echo "hit_count=0" >>"$GITHUB_OUTPUT"
	}
	exit 0
fi

echo "check_forbidden_strings: ${hit_count} violation(s)" >&2
[[ -n "${GITHUB_OUTPUT:-}" ]] && {
	echo "found=true" >>"$GITHUB_OUTPUT"
	echo "hit_count=${hit_count}" >>"$GITHUB_OUTPUT"
}
exit 1
