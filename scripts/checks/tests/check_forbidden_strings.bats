#!/usr/bin/env bats
# Mocked end-to-end test for check_forbidden_strings.bash: runs the real
# script (which itself shells out to the real, sibling find_strings.bash)
# against real fixture files under BATS_TEST_TMPDIR. As with
# find_strings.bats, git/grep/find are exercised for real rather than
# mocked, since that is exactly the behavior under test.
#
# check_forbidden_strings.bash forwards --search-path straight through to
# find_strings.bash, which still decides its git-aware vs. find-based
# branch from its OWN current working directory - so the same cd-into-a-
# fresh-BATS_TEST_TMPDIR-for-the-fallback-branch approach from
# find_strings.bats applies here too.

SCRIPT="$BATS_TEST_DIRNAME/../check_forbidden_strings.bash"

setup() {
    cd "$BATS_TEST_TMPDIR" || exit 1
}

@test "reports a GitHub error annotation per hit and exits 1 when violations are found" {
    mkdir -p fixture
    printf 'line one\nhas a BADWORD in it\n' >fixture/a.txt

    run "$SCRIPT" --pattern BADWORD --search-path fixture
    [ "$status" -eq 1 ]
    [[ "$output" == *"::error file=fixture/a.txt,line=2,title=Forbidden string(s) found in repository::Forbidden string BADWORD (U+0042,U+0041,U+0044,U+0057,U+004F,U+0052,U+0044) at fixture/a.txt:2: has a BADWORD in it"* ]]
    [[ "$output" == *"check_forbidden_strings: 1 violation(s) total"* ]]
}

@test "exits 0 with no annotations when nothing matches" {
    mkdir -p fixture
    printf 'nothing forbidden here\n' >fixture/a.txt

    run "$SCRIPT" --pattern BADWORD --search-path fixture
    [ "$status" -eq 0 ]
    [[ "$output" != *"::error"* ]]
    [[ "$output" == *"check_forbidden_strings: no violations"* ]]
}

@test "multiple --pattern flags each get their own hit count in the summary" {
    mkdir -p fixture
    printf 'has FOO here\nand BAR there\nand another FOO\n' >fixture/a.txt

    run "$SCRIPT" --pattern FOO --pattern BAR --search-path fixture
    [ "$status" -eq 1 ]
    [[ "$output" == *"check_forbidden_strings: 3 violation(s) total"* ]]
    [[ "$output" == *"FOO"*": 2 hit(s)"* ]]
    [[ "$output" == *"BAR"*": 1 hit(s)"* ]]
}

@test "a custom --error-message is used as the annotation title" {
    mkdir -p fixture
    printf 'has BADWORD here\n' >fixture/a.txt

    run "$SCRIPT" --pattern BADWORD --search-path fixture --error-message "custom failure message"
    [ "$status" -eq 1 ]
    [[ "$output" == *"title=custom failure message::"* ]]
}

@test "--exclude-dir and --exclude-glob are forwarded through to find_strings.bash" {
    mkdir -p fixture/keep fixture/vendor
    printf 'has BADWORD here\n' >fixture/keep/a.txt
    printf 'has BADWORD here\n' >fixture/vendor/b.txt
    printf 'has BADWORD here\n' >fixture/keep/ignore.log

    run "$SCRIPT" --pattern BADWORD --search-path fixture --exclude-dir vendor --exclude-glob '*.log'
    [ "$status" -eq 1 ]
    [[ "$output" == *"fixture/keep/a.txt"* ]]
    [[ "$output" != *"fixture/vendor"* ]]
    [[ "$output" != *"ignore.log"* ]]
}

@test "exits 2 when no --pattern is given" {
    run "$SCRIPT" --search-path fixture
    [ "$status" -eq 2 ]
    [[ "$output" == *"at least one --pattern is required"* ]]
}

@test "exits 2 on an unknown argument" {
    run "$SCRIPT" --pattern BADWORD --nonsense
    [ "$status" -eq 2 ]
    [[ "$output" == *"unknown argument: --nonsense"* ]]
}

@test "-h/--help exits 0 and prints usage without requiring --pattern" {
    run "$SCRIPT" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage:"* ]]
}
