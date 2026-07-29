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
Hit counts are printed on stderr.

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

print_summary() {
	local pattern_field count

	if ((hit_count > 0)); then
		echo "check_forbidden_strings: ${hit_count} violation(s) total" >&2
		for pattern_field in "${pattern_fields_seen[@]}"; do
			count="${pattern_hit_counts[$pattern_field]:-0}"
			echo "  ${pattern_field}: ${count} hit(s)" >&2
		done
	else
		echo "check_forbidden_strings: no violations" >&2
	fi
}

args=(--search-path "$search_path" --no-summary)
for dir in "${exclude_dirs[@]}"; do args+=(--exclude-dir "$dir"); done
for glob in "${exclude_globs[@]}"; do args+=(--exclude-glob "$glob"); done
for pattern in "${patterns[@]}"; do args+=(--pattern "$pattern"); done

found=false
hit_count=0
declare -A pattern_hit_counts=()
pattern_fields_seen=()

while IFS=$'\t' read -r file line pattern_field content; do
	[[ -z "$file" ]] && continue

	found=true
	hit_count=$((hit_count + 1))

	if [[ -z "${pattern_hit_counts[$pattern_field]+x}" ]]; then
		pattern_fields_seen+=("$pattern_field")
	fi
	pattern_hit_counts["$pattern_field"]=$((${pattern_hit_counts["$pattern_field"]:-0} + 1))

	echo "::error file=${file},line=${line},title=${error_message}::Forbidden string ${pattern_field} at ${file}:${line}: ${content}"
done < <("$FIND_STRINGS" "${args[@]}")

print_summary

if [[ "$found" != true ]]; then
	exit 0
fi

exit 1
