#!/usr/bin/env bash
set -euo pipefail

usage() {
	cat <<'EOF'
Usage:
    find_strings.bash \
        --pattern STRING [--pattern STRING ...] \
        [--search-path PATH] \
        [--exclude-dir DIR ...] \
        [--exclude-glob GLOB ...]

Search recursively for one or more literal strings under PATH.

In a git repository:
    - tracked files (including unstaged edits) are searched with git grep
    - untracked, non-ignored files are searched with grep

Outside a git repository:
    - all files are searched with find + grep

Output (stdout, one match per line; empty if none):
    <file>	TAB<line>	TAB<pattern>	TAB<line-content>

Default excludes (non-git fallback only, merged with --exclude-dir):
    .git, node_modules, dist, build, .venv, .pytest-logs

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

grep_args=(-n -F)
file_grep_args=(-H -n -I -F)
for pattern in "${patterns[@]}"; do
	grep_args+=(-e "$pattern")
	file_grep_args+=(-e "$pattern")
done

scan_tracked_files() {
	# Working-tree content for tracked files (includes unstaged edits).
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
		echo "find_strings: git repo — tracked via git grep, untracked via grep" >&2
		scan_tracked_files
		scan_untracked_files
	else
		echo "find_strings: not a git repo — using find + grep" >&2
		scan_with_find
	fi
}

exit_code=1

while IFS= read -r hit; do
	[[ -z "$hit" ]] && continue

	file="${hit%%:*}"
	rest="${hit#*:}"
	line="${rest%%:*}"
	content="${rest#*:}"

	# git grep / grep with multiple -e does not label which pattern matched.
	for pattern in "${patterns[@]}"; do
		if [[ "$content" == *"$pattern"* ]]; then
			exit_code=0
			printf '%s\t%s\t%s\t%s\n' "$file" "$line" "$pattern" "$content"
		fi
	done
done < <(run_scan 2>/dev/null || true)

exit "$exit_code"
