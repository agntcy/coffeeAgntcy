#!/usr/bin/env bats
# Mocked end-to-end test for check_dashes.bash: a thin wrapper that execs
# the real, sibling check_forbidden_strings.bash with the em-dash/en-dash
# patterns pinned in. Tested end-to-end for real (no mocking) against
# fixture files under BATS_TEST_TMPDIR.
#
# check_dashes.bash takes no arguments of its own (it does not forward
# "$@" to check_forbidden_strings.bash at all), so there is no
# --search-path to pass - the fixture directory itself is made the
# current working directory, and check_forbidden_strings.bash's own
# default search path of "." covers it.
#
# The em dash (U+2014) and en dash (U+2013) are never typed as literal
# characters in this file (that would itself trip this repo's own
# no-em-en-dashes rule); they are produced programmatically with
# $'\uXXXX' escapes instead.

SCRIPT="$BATS_TEST_DIRNAME/../check_dashes.bash"

EM_DASH=$'\u2014'
EN_DASH=$'\u2013'

setup() {
    cd "$BATS_TEST_TMPDIR" || exit 1
}

@test "exits 1 and reports a hit when a file contains an em dash" {
    printf 'a sentence%sbroken by an em dash\n' "$EM_DASH" >a.txt

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"::error"* ]]
    [[ "$output" == *"en dash or em dash"* ]]
    [[ "$output" == *"a.txt"* ]]
}

@test "exits 1 and reports a hit when a file contains an en dash" {
    printf 'a range of 1%s10\n' "$EN_DASH" >a.txt

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"::error"* ]]
    [[ "$output" == *"a.txt"* ]]
}

@test "exits 0 with no hits when no file contains an em dash or en dash" {
    printf 'a perfectly plain sentence - with a plain hyphen\n' >a.txt

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" != *"::error"* ]]
}

@test "counts em dashes and en dashes separately when both are present" {
    # each hit is counted per matching line, so the two dash kinds are put
    # on separate lines to get distinguishable, meaningful counts (2 vs 1)
    # rather than both landing on one shared line.
    printf 'first em%sdash line\nsecond em%sdash line\nan en%sdash line\n' \
        "$EM_DASH" "$EM_DASH" "$EN_DASH" >a.txt

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *": 2 hit(s)"* ]]
    [[ "$output" == *": 1 hit(s)"* ]]
}
