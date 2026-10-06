#!/usr/bin/env bats
# Mocked end-to-end test for fix_dashes.bash: a thin wrapper that calls
# the real, sibling find_strings.bash directly with --replace-with '-'
# and --write, pinned to the em-dash/en-dash patterns. Tested end-to-end
# for real (no mocking) against fixture files under BATS_TEST_TMPDIR.
#
# fix_dashes.bash takes no arguments of its own and always operates
# against find_strings.bash's default search path of ".", so each test
# makes a fixture subdirectory of BATS_TEST_TMPDIR the current working
# directory - keeping a sibling directory (also under BATS_TEST_TMPDIR,
# never above it) to prove containment without writing anywhere outside
# this test's own isolated tmpdir.
#
# The em dash (U+2014) and en dash (U+2013) are never typed as literal
# characters in this file (that would itself trip this repo's own
# no-em-en-dashes rule); they are produced programmatically with
# $'\uXXXX' escapes instead.

SCRIPT="$BATS_TEST_DIRNAME/../fix_dashes.bash"

EM_DASH=$'\u2014'
EN_DASH=$'\u2013'

setup() {
    mkdir -p "$BATS_TEST_TMPDIR/scan"
    cd "$BATS_TEST_TMPDIR/scan" || exit 1
}

@test "replaces an em dash with a plain hyphen in the fixture file's content" {
    printf 'a sentence%sbroken by an em dash\n' "$EM_DASH" >a.txt

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"find_strings: fixed ./a.txt"* ]]

    run cat a.txt
    [ "$output" = "a sentence-broken by an em dash" ]
}

@test "replaces an en dash with a plain hyphen in the fixture file's content" {
    printf 'a range of 1%s10\n' "$EN_DASH" >a.txt

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"find_strings: fixed ./a.txt"* ]]

    run cat a.txt
    [ "$output" = "a range of 1-10" ]
}

@test "replaces both em dashes and en dashes across multiple files in one run" {
    printf 'first em%sdash line\n' "$EM_DASH" >a.txt
    printf 'an en%sdash line\n' "$EN_DASH" >b.txt

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"find_strings: fixed ./a.txt"* ]]
    [[ "$output" == *"find_strings: fixed ./b.txt"* ]]

    run cat a.txt
    [ "$output" = "first em-dash line" ]
    run cat b.txt
    [ "$output" = "an en-dash line" ]
}

@test "reports nothing to fix and exits 0 on a clean fixture" {
    printf 'a perfectly plain sentence - with a plain hyphen\n' >a.txt

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"No en dash or em dash found - nothing to fix."* ]]

    run cat a.txt
    [ "$output" = "a perfectly plain sentence - with a plain hyphen" ]
}

@test "leaves an unrelated file outside the current directory untouched" {
    mkdir -p ../outside-fixture
    printf 'has an em%sdash too\n' "$EM_DASH" >../outside-fixture/other.txt
    printf 'a clean file\n' >a.txt

    run "$SCRIPT"
    [ "$status" -eq 0 ]

    run cat ../outside-fixture/other.txt
    [ "$output" = "has an em${EM_DASH}dash too" ]
}
