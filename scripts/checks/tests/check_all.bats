#!/usr/bin/env bats
# Mocked end-to-end test for check_all.bash: it computes SCRIPT_DIR/
# LINT_DIR from its own location and invokes every sibling check by
# real relative path (not by name on PATH), so it's exercised here via
# the fixture-copy trick, but with trivial FAKE stand-in scripts in
# place of the real siblings instead of the real check_dashes.bash,
# check_markdown_links.bash, etc. - this test is only about check_all's
# own orchestration (parallel run-to-completion, exit code aggregation,
# per-check log sectioning, summary table), not about any individual
# check's real logic.

FIXTURE_REPO="$BATS_TEST_TMPDIR/repo"

setup() {
    mkdir -p "$FIXTURE_REPO/scripts/checks"
    mkdir -p "$FIXTURE_REPO/scripts/lint"
    cp "$BATS_TEST_DIRNAME/../check_all.bash" "$FIXTURE_REPO/scripts/checks/check_all.bash"
    chmod +x "$FIXTURE_REPO/scripts/checks/check_all.bash"
    SCRIPT="$FIXTURE_REPO/scripts/checks/check_all.bash"
}

# Writes a trivial fake stand-in script at $1 that echoes $2 and exits $3.
write_fake() {
    local path="$1" message="$2" exit_code="$3"
    cat >"$path" <<EOF
#!/usr/bin/env bash
echo "$message"
exit $exit_code
EOF
    chmod +x "$path"
}

# Plants a fake for every sibling check_all.bash invokes, each passing
# (exit 0) with an identifiable message, unless overridden per-test.
write_all_passing_fakes() {
    write_fake "$FIXTURE_REPO/scripts/checks/check_dashes.bash" "fake dashes output" 0
    write_fake "$FIXTURE_REPO/scripts/lint/lint_shell.bash" "fake shell lint output" 0
    write_fake "$FIXTURE_REPO/scripts/lint/lint_workflows.bash" "fake workflow lint output" 0
    write_fake "$FIXTURE_REPO/scripts/checks/check_workflow_permissions.bash" "fake permissions output" 0
    write_fake "$FIXTURE_REPO/scripts/checks/check_markdown_links.bash" "fake links output" 0
    write_fake "$FIXTURE_REPO/scripts/checks/check_pinned_references.bash" "fake pins output" 0
    write_fake "$FIXTURE_REPO/scripts/checks/check_helm_chart_versions.bash" "fake helm output" 0
    write_fake "$FIXTURE_REPO/scripts/checks/check_pipeline_exceptions.bash" "fake pipeline output" 0
    write_fake "$FIXTURE_REPO/scripts/checks/check_uv_locks.bash" "fake locks output" 0
    write_fake "$FIXTURE_REPO/scripts/checks/check_bash_tests.bash" "fake bash tests output" 0
    write_fake "$FIXTURE_REPO/scripts/checks/check_bash_test_coverage.bash" "fake coverage output" 0
}

@test "passes overall and shows PASS for every check when all checks succeed" {
    write_all_passing_fakes

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"All checks passed."* ]]
    [[ "$output" == *"PASS: dashes:check"* ]]
    [[ "$output" == *"PASS: shell:lint"* ]]
    [[ "$output" == *"PASS: workflows:lint"* ]]
    [[ "$output" == *"PASS: workflows:check-permissions"* ]]
    [[ "$output" == *"PASS: links:check"* ]]
    [[ "$output" == *"PASS: pins:check"* ]]
    [[ "$output" == *"PASS: helm:check-versions"* ]]
    [[ "$output" == *"PASS: pipeline:check-exceptions"* ]]
    [[ "$output" == *"PASS: locks:check"* ]]
    [[ "$output" == *"PASS: tests:bash"* ]]
    [[ "$output" == *"PASS: tests:coverage"* ]]
}

@test "each check's own output appears within its own labeled section, in order" {
    write_all_passing_fakes

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"=== dashes:check ==="*"fake dashes output"*"=== shell:lint ==="*"fake shell lint output"*"=== workflows:lint ==="*"fake workflow lint output"* ]]
    [[ "$output" == *"=== links:check ==="*"fake links output"*"=== pins:check ==="*"fake pins output"* ]]
}

@test "fails overall when exactly one check fails, while every other check still runs and shows PASS" {
    write_all_passing_fakes
    write_fake "$FIXTURE_REPO/scripts/checks/check_markdown_links.bash" "fake links output: broken link found" 1

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"FAIL: links:check (exit 1)"* ]]
    [[ "$output" == *"=== links:check ==="*"fake links output: broken link found"* ]]

    # Never-fail-fast: every other check still ran to completion and
    # still reports PASS, even though one check failed.
    [[ "$output" == *"PASS: dashes:check"* ]]
    [[ "$output" == *"PASS: shell:lint"* ]]
    [[ "$output" == *"PASS: workflows:lint"* ]]
    [[ "$output" == *"PASS: workflows:check-permissions"* ]]
    [[ "$output" == *"PASS: pins:check"* ]]
    [[ "$output" == *"PASS: helm:check-versions"* ]]
    [[ "$output" == *"PASS: pipeline:check-exceptions"* ]]
    [[ "$output" == *"PASS: locks:check"* ]]
    [[ "$output" == *"PASS: tests:bash"* ]]
    [[ "$output" == *"PASS: tests:coverage"* ]]
    [[ "$output" != *"All checks passed."* ]]
}

@test "fails overall and reports each check's own exit code when multiple checks fail simultaneously" {
    write_all_passing_fakes
    write_fake "$FIXTURE_REPO/scripts/checks/check_dashes.bash" "fake dashes output: em-dash found" 1
    write_fake "$FIXTURE_REPO/scripts/checks/check_pinned_references.bash" "fake pins output: unpinned ref found" 2
    write_fake "$FIXTURE_REPO/scripts/checks/check_bash_test_coverage.bash" "fake coverage output: script has no test" 1

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"FAIL: dashes:check (exit 1)"* ]]
    [[ "$output" == *"FAIL: pins:check (exit 2)"* ]]
    [[ "$output" == *"FAIL: tests:coverage (exit 1)"* ]]

    # The checks that didn't fail still ran to completion and still
    # show PASS - all ten checks are accounted for regardless of how
    # many of their siblings failed.
    [[ "$output" == *"PASS: shell:lint"* ]]
    [[ "$output" == *"PASS: workflows:lint"* ]]
    [[ "$output" == *"PASS: workflows:check-permissions"* ]]
    [[ "$output" == *"PASS: links:check"* ]]
    [[ "$output" == *"PASS: helm:check-versions"* ]]
    [[ "$output" == *"PASS: pipeline:check-exceptions"* ]]
    [[ "$output" == *"PASS: locks:check"* ]]
    [[ "$output" == *"PASS: tests:bash"* ]]
    [[ "$output" != *"All checks passed."* ]]
}
