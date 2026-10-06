#!/usr/bin/env bats
# Mocked end-to-end test for check_markdown_links.bash: the script uses
# `git ls-files -- "*.md"` (not a plain filesystem walk) to find every
# markdown file to scan, and computes its own REPO_ROOT from
# BASH_SOURCE before cd'ing there. Both mean the fixture must be a real,
# initialized git repository, built with the same fixture-copy trick
# used elsewhere: a real copy of the script at the same relative depth
# (scripts/checks/) inside a throwaway git repo, with fake .md files
# staged via `git add` (verified empirically that `git ls-files` already
# shows staged-but-uncommitted files, so no commit is needed).

FIXTURE_REPO="$BATS_TEST_TMPDIR/repo"

setup() {
    mkdir -p "$FIXTURE_REPO/scripts/checks"
    cp "$BATS_TEST_DIRNAME/../check_markdown_links.bash" \
        "$FIXTURE_REPO/scripts/checks/check_markdown_links.bash"
    chmod +x "$FIXTURE_REPO/scripts/checks/check_markdown_links.bash"
    SCRIPT="$FIXTURE_REPO/scripts/checks/check_markdown_links.bash"

    git -C "$FIXTURE_REPO" init -q
    git -C "$FIXTURE_REPO" config user.email "test@example.com"
    git -C "$FIXTURE_REPO" config user.name "Test"
}

stage_all() {
    git -C "$FIXTURE_REPO" add -A
}

@test "passes when a relative link resolves to a real file" {
    printf 'target file\n' >"$FIXTURE_REPO/target.md"
    printf '[valid link](target.md)\n' >"$FIXTURE_REPO/doc.md"
    stage_all

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: every relative link"* ]]
}

@test "fails, naming file and line, when a relative link is broken" {
    printf '[broken link](missing.md)\n' >"$FIXTURE_REPO/doc.md"
    stage_all

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"doc.md:1: 'missing.md' does not resolve to an existing file"* ]]
}

@test "resolves a root-relative link from the fixture repo's root" {
    printf 'root target\n' >"$FIXTURE_REPO/root-target.md"
    mkdir -p "$FIXTURE_REPO/nested/dir"
    printf '[root link](/root-target.md)\n' >"$FIXTURE_REPO/nested/dir/doc.md"
    stage_all

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: every relative link"* ]]
}

@test "skips an http(s) link even when it looks broken" {
    printf '[http link](https://example.com/does/not/exist)\n' >"$FIXTURE_REPO/doc.md"
    stage_all

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: every relative link"* ]]
}

@test "skips a GitHub blob/tree/raw web path" {
    printf '[gh blob](/owner/repo/blob/main/does-not-exist.md)\n' >"$FIXTURE_REPO/doc.md"
    stage_all

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: every relative link"* ]]
}

@test "skips a target containing a placeholder segment" {
    printf '[placeholder](path/<rule>.md)\n' >"$FIXTURE_REPO/doc.md"
    stage_all

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: every relative link"* ]]
}

@test "a link-exempt comment with a stated reason suppresses an otherwise-broken link" {
    printf '[exempt link](missing.md) <!-- link-exempt: not applicable in this fixture -->\n' \
        >"$FIXTURE_REPO/doc.md"
    stage_all

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: every relative link"* ]]
}

@test "a link-exempt comment with no stated reason produces an error itself" {
    printf '[exempt link](target.md) <!-- link-exempt: -->\n' >"$FIXTURE_REPO/doc.md"
    printf 'target file\n' >"$FIXTURE_REPO/target.md"
    stage_all

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"doc.md:1: 'link-exempt' comment must state a reason"* ]]
}
