#!/usr/bin/env bash
set -euo pipefail

usage() {
	cat <<'EOF'
Usage:
    find_strings.bash \
        --pattern STRING [--pattern STRING ...] \
        [--search-path PATH] \
        [--exclude-dir DIR ...] \
        [--exclude-glob GLOB ...] \
        [--replace-with TEXT] \
        [--write] \
        [--no-summary]

Search recursively for one or more literal strings under PATH.

In a git repository:
    - tracked files (including unstaged edits) are searched with git grep
    - untracked, non-ignored files are searched with grep

Outside a git repository:
    - all files are searched with find + grep

Output (stdout, one match per line; empty if none):
    <file>  TAB<line>  TAB<pattern> (U+XXXX)  TAB<line-content>

Summary (stderr, unless --no-summary):
    find_strings: N hit(s) total
      --pattern X (U+XXXX): M hit(s)

Default excludes (non-git fallback only, merged with --exclude-dir):
    .git, node_modules, dist, build, .venv, .pytest-logs

Options:
    --replace-with TEXT   replace matched pattern(s) in affected files
    --write               apply edits (default: dry-run, files listed on stderr)
    --no-summary          suppress stderr hit-count summary (TSV still printed)

Exit codes:
    0 = one or more matches
    1 = no matches
    2 = invalid args or search path missing
EOF
}

search_path="."
patterns=()
exclude_dirs=()
exclude_globs=()
default_exclude_dirs=(.git node_modules dist build .venv .pytest-logs)
show_summary=true
fix_replacement=""
fix_write=false

while [[ $# -gt 0 ]]; do
	case "$1" in
	--pattern)
		[[ $# -ge 2 ]] || {
			usage >&2
			exit 2
		}
		patterns+=("$2")
		shift 2
		;;
	--search-path)
		[[ $# -ge 2 ]] || {
			usage >&2
			exit 2
		}
		search_path="$2"
		shift 2
		;;
	--exclude-dir)
		[[ $# -ge 2 ]] || {
			usage >&2
			exit 2
		}
		exclude_dirs+=("$2")
		shift 2
		;;
	--exclude-glob)
		[[ $# -ge 2 ]] || {
			usage >&2
			exit 2
		}
		exclude_globs+=("$2")
		shift 2
		;;
	--replace-with)
		[[ $# -ge 2 ]] || {
			usage >&2
			exit 2
		}
		fix_replacement="$2"
		shift 2
		;;
	--write)
		fix_write=true
		shift
		;;
	--no-summary)
		show_summary=false
		shift
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
	usage >&2
	exit 2
fi

if [[ ! -e "$search_path" ]]; then
	echo "search path does not exist: $search_path" >&2
	exit 2
fi

declare -A pattern_unicode_cache=()

warm_pattern_unicode_cache() {
	local pattern char
	local -a codes=()

	for pattern in "${patterns[@]}"; do
		[[ -n "${pattern_unicode_cache[$pattern]+x}" ]] && continue

		if [[ ${#pattern} -eq 1 ]]; then
			pattern_unicode_cache["$pattern"]="U+$(printf '%04X' $(( $(printf '%d' "'$pattern") )) )"
			continue
		fi

		codes=()
		while IFS= read -r -n1 char; do
			[[ -z "$char" ]] && continue
			codes+=("U+$(printf '%04X' $(( $(printf '%d' "'$char") )) )")
		done <<<"$pattern"
		local IFS=,
		pattern_unicode_cache["$pattern"]="${codes[*]}"
	done
}

warm_pattern_unicode_cache

grep_args=(-n -F)
file_grep_args=(-H -n -I -F)
for pattern in "${patterns[@]}"; do
	grep_args+=(-e "$pattern")
	file_grep_args+=(-e "$pattern")
done

scan_tracked_files() {
	git grep "${grep_args[@]}" -I -- "$search_path" || true
}

scan_untracked_files() {
	local untracked=()

	while IFS= read -r -d '' file; do
		untracked+=("$file")
	done < <(git ls-files --others --exclude-standard -z -- "$search_path")

	if ((${#untracked[@]} == 0)); then
		return 0
	fi

	grep "${file_grep_args[@]}" -- "${untracked[@]}" 2>/dev/null || true
}

scan_with_find() {
	local find_exclude_dirs=("${default_exclude_dirs[@]}" "${exclude_dirs[@]}")
	local find_args=(-P "$search_path")

	if ((${#find_exclude_dirs[@]} > 0)); then
		find_args+=(\( )
		for dir in "${find_exclude_dirs[@]}"; do
			find_args+=(-name "$dir" -o)
		done
		find_args+=(-false \) -prune -o)
	fi

	find_args+=(-type f)

	for glob in "${exclude_globs[@]}"; do
		find_args+=(! -name "$glob")
	done

	find_args+=(-exec grep -H -I "${grep_args[@]}" {} +)
	find "${find_args[@]}"
}

run_scan() {
	if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
		echo "find_strings: git repo - tracked via git grep, untracked via grep" >&2
		scan_tracked_files
		scan_untracked_files
	else
		echo "find_strings: not a git repo - using find + grep" >&2
		scan_with_find
	fi
}

print_summary() {
	local pattern count

	if [[ "$show_summary" != true ]]; then
		return 0
	fi

	if ((hit_count > 0)); then
		echo "find_strings: ${hit_count} hit(s) total" >&2
		for pattern in "${patterns[@]}"; do
			count="${pattern_hit_counts[$pattern]:-0}"
			((count > 0)) || continue
			echo "  --pattern ${pattern} (${pattern_unicode_cache[$pattern]}): ${count} hit(s)" >&2
		done
	else
		echo "find_strings: no hits" >&2
	fi
}

apply_replacements() {
	local file pattern hex perl_script=""

	[[ -n "$fix_replacement" ]] || return 0
	((${#files_to_fix[@]} == 0)) && return 0

	for pattern in "${patterns[@]}"; do
		if [[ ${#pattern} -ne 1 ]]; then
			echo "find_strings: --replace-with supports single-character --pattern only" >&2
			exit 2
		fi
		hex="${pattern_unicode_cache[$pattern]#U+}"
		perl_script+="s/\\x{${hex}}/\$ENV{FIX_REPL}/g; "
	done

	export FIX_REPL="$fix_replacement"

	for file in "${!files_to_fix[@]}"; do
		if [[ "$fix_write" == true ]]; then
			perl -CSD -i -pe "$perl_script" -- "$file"
			echo "find_strings: fixed ${file}" >&2
		else
			echo "find_strings: would fix ${file}" >&2
		fi
	done
}

exit_code=1
hit_count=0
declare -A pattern_hit_counts=()
declare -A files_to_fix=()

while IFS= read -r hit; do
	[[ -z "$hit" ]] && continue

	file="${hit%%:*}"
	rest="${hit#*:}"
	line="${rest%%:*}"
	content="${rest#*:}"

	for pattern in "${patterns[@]}"; do
		if [[ "$content" == *"$pattern"* ]]; then
			exit_code=0
			hit_count=$((hit_count + 1))
			pattern_hit_counts["$pattern"]=$((${pattern_hit_counts["$pattern"]:-0} + 1))
			files_to_fix["$file"]=1
			printf '%s\t%s\t%s (%s)\t%s\n' \
				"$file" "$line" "$pattern" "${pattern_unicode_cache[$pattern]}" "$content"
		fi
	done
done < <(run_scan 2>/dev/null || true)

apply_replacements
print_summary
exit "$exit_code"
