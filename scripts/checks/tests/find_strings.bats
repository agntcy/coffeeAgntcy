#!/usr/bin/env bats
# Mocked end-to-end test for find_strings.bash: runs the real script as a
# subprocess against real fixture files under BATS_TEST_TMPDIR. git, grep,
# find and perl are exercised for real (not mocked) since orchestrating
# those exact tools against real file content is this script's whole job -
# there is nothing left to test if they are stubbed out.
#
# The script picks its git-aware branch vs. its find-based fallback branch
# by running `git rev-parse --is-inside-work-tree` from its OWN current
# working directory (not from --search-path). BATS_TEST_TMPDIR itself sits
# outside this repo's git work tree (confirmed empirically: a fresh test
# tmpdir reports "not a git repository"), so cd-ing into it gives the
# fallback branch for free; git-initializing it first gives the git-aware
# branch instead.

bats_require_minimum_version 1.5.0

SCRIPT="$BATS_TEST_DIRNAME/../find_strings.bash"

setup() {
    cd "$BATS_TEST_TMPDIR" || exit 1
}

git_init_fixture() {
    git init -q .
    git config user.email "test@example.com"
    git config user.name "Test User"
}

# --- non-git fallback branch (find + grep) ---------------------------------

@test "non-git: reports each hit and a per-pattern summary count" {
    mkdir -p fixture
    printf 'line one\nline with X mark\nanother X here\n' >fixture/a.txt
    printf 'no match here\n' >fixture/b.txt

    run "$SCRIPT" --pattern X --search-path fixture
    [ "$status" -eq 0 ]
    [[ "$output" == *$'fixture/a.txt\t2\tX (U+0058)\tline with X mark'* ]]
    [[ "$output" == *$'fixture/a.txt\t3\tX (U+0058)\tanother X here'* ]]
    [[ "$output" != *"fixture/b.txt"* ]]
    [[ "$output" == *"find_strings: 2 hit(s) total"* ]]
    [[ "$output" == *"--pattern X (U+0058): 2 hit(s)"* ]]
}

@test "non-git: multiple --pattern flags match any pattern and track separate counts" {
    mkdir -p fixture
    printf 'contains TODO marker\n' >fixture/a.txt
    printf 'contains FIXME marker\nand another FIXME\n' >fixture/b.txt
    printf 'contains neither\n' >fixture/c.txt

    run "$SCRIPT" --pattern TODO --pattern FIXME --search-path fixture
    [ "$status" -eq 0 ]
    [[ "$output" == *"fixture/a.txt"*"TODO"* ]]
    [[ "$output" == *"fixture/b.txt"*"FIXME"* ]]
    [[ "$output" != *"fixture/c.txt"* ]]
    [[ "$output" == *"find_strings: 3 hit(s) total"* ]]
    [[ "$output" == *"--pattern TODO"*": 1 hit(s)"* ]]
    [[ "$output" == *"--pattern FIXME"*": 2 hit(s)"* ]]
}

@test "non-git: --exclude-dir excludes a whole directory from the scan" {
    mkdir -p fixture/keep fixture/vendor
    printf 'has an X in it\n' >fixture/keep/a.txt
    printf 'has an X in it\n' >fixture/vendor/b.txt

    run "$SCRIPT" --pattern X --search-path fixture --exclude-dir vendor
    [ "$status" -eq 0 ]
    [[ "$output" == *"fixture/keep/a.txt"* ]]
    [[ "$output" != *"fixture/vendor"* ]]
}

@test "non-git: --exclude-glob excludes files by name from the scan" {
    mkdir -p fixture
    printf 'has an X in it\n' >fixture/keep.txt
    printf 'has an X in it\n' >fixture/ignore.log

    run "$SCRIPT" --pattern X --search-path fixture --exclude-glob '*.log'
    [ "$status" -eq 0 ]
    [[ "$output" == *"fixture/keep.txt"* ]]
    [[ "$output" != *"fixture/ignore.log"* ]]
}

@test "non-git: --replace-with without --write is a dry run that leaves file content untouched" {
    mkdir -p fixture
    printf 'has ZZ marks\n' >fixture/target.txt

    run "$SCRIPT" --pattern Z --search-path fixture --replace-with z
    [ "$status" -eq 0 ]
    [[ "$output" == *"find_strings: would fix fixture/target.txt"* ]]
    [[ "$output" != *"find_strings: fixed"* ]]

    run cat fixture/target.txt
    [ "$output" = "has ZZ marks" ]
}

@test "non-git: --replace-with --write rewrites matched characters, only inside the search path" {
    mkdir -p fixture outside
    printf 'has ZZ marks\n' >fixture/target.txt
    printf 'has ZZ marks too\n' >outside/other.txt

    run "$SCRIPT" --pattern Z --search-path fixture --replace-with z --write
    [ "$status" -eq 0 ]
    [[ "$output" == *"find_strings: fixed fixture/target.txt"* ]]

    run cat fixture/target.txt
    [ "$output" = "has zz marks" ]

    # untouched: outside the search path entirely, never scanned
    run cat outside/other.txt
    [ "$output" = "has ZZ marks too" ]
}

@test "non-git: --no-summary suppresses the stderr summary but keeps TSV on stdout" {
    mkdir -p fixture
    printf 'has an X in it\n' >fixture/a.txt

    run --separate-stderr "$SCRIPT" --pattern X --search-path fixture --no-summary
    [ "$status" -eq 0 ]
    [[ "$output" == *$'fixture/a.txt\t1\tX (U+0058)\thas an X in it'* ]]
    [[ "$stderr" != *"hit(s) total"* ]]
}

@test "non-git: exits 1 and prints no TSV rows when nothing matches" {
    mkdir -p fixture
    printf 'nothing to see here\n' >fixture/a.txt

    run "$SCRIPT" --pattern X --search-path fixture
    [ "$status" -eq 1 ]
    [[ "$output" != *$'\t'* ]]
    [[ "$output" == *"find_strings: no hits"* ]]
}

@test "exits 2 when no --pattern is given" {
    run "$SCRIPT" --search-path .
    [ "$status" -eq 2 ]
    [[ "$output" == *"at least one --pattern is required"* ]]
}

@test "exits 2 when --search-path does not exist" {
    run "$SCRIPT" --pattern X --search-path ./no-such-fixture-dir
    [ "$status" -eq 2 ]
    [[ "$output" == *"search path does not exist"* ]]
}

@test "exits 2 on an unknown argument" {
    run "$SCRIPT" --pattern X --nonsense
    [ "$status" -eq 2 ]
    [[ "$output" == *"unknown argument: --nonsense"* ]]
}

@test "-h/--help exits 0 and prints usage without requiring --pattern" {
    run "$SCRIPT" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage:"* ]]
}

@test "--replace-with rejects a multi-character --pattern even though plain matching allows it" {
    mkdir -p fixture
    printf 'has an AB marker\n' >fixture/target.txt

    run "$SCRIPT" --pattern AB --search-path fixture --replace-with X
    [ "$status" -eq 2 ]
    [[ "$output" == *"--replace-with supports single-character --pattern only"* ]]

    run cat fixture/target.txt
    [ "$output" = "has an AB marker" ]
}

# --- git-aware branch (git grep for tracked, grep for untracked) -----------

@test "git: searches both tracked (git grep) and untracked non-ignored (grep) files" {
    git_init_fixture
    printf 'tracked line with X\n' >tracked.txt
    git add tracked.txt
    git commit -q -m "add tracked fixture"
    printf 'untracked line with X\n' >untracked.txt

    run "$SCRIPT" --pattern X --search-path .
    [ "$status" -eq 0 ]
    [[ "$output" == *"tracked.txt"*"X"* ]]
    [[ "$output" == *"untracked.txt"*"X"* ]]
    [[ "$output" == *"find_strings: 2 hit(s) total"* ]]
}

@test "git: git grep sees an unstaged edit to a tracked file, not just its committed content" {
    git_init_fixture
    printf 'no marker yet\n' >tracked.txt
    git add tracked.txt
    git commit -q -m "add tracked fixture without the marker"

    # unstaged edit: adds the marker without staging or committing it
    printf 'no marker yet\nnow has X too\n' >tracked.txt

    run "$SCRIPT" --pattern X --search-path .
    [ "$status" -eq 0 ]
    [[ "$output" == *"tracked.txt"*"X"* ]]
}

@test "git: an untracked but gitignored file is not searched" {
    git_init_fixture
    printf 'ignored.txt\n' >.gitignore
    git add .gitignore
    git commit -q -m "add gitignore"
    printf 'tracked line with X\n' >tracked.txt
    git add tracked.txt
    git commit -q -m "add tracked fixture"
    printf 'ignored line with X\n' >ignored.txt

    run "$SCRIPT" --pattern X --search-path .
    [ "$status" -eq 0 ]
    [[ "$output" == *"tracked.txt"* ]]
    [[ "$output" != *"ignored.txt"* ]]
}

@test "git: --write rewrites a tracked file's working-tree content" {
    git_init_fixture
    printf 'has QQ marks\n' >tracked.txt
    git add tracked.txt
    git commit -q -m "add tracked fixture"

    run "$SCRIPT" --pattern Q --search-path . --replace-with q --write
    [ "$status" -eq 0 ]
    [[ "$output" == *"find_strings: fixed tracked.txt"* ]]

    run cat tracked.txt
    [ "$output" = "has qq marks" ]
}
