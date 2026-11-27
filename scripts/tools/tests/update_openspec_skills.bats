#!/usr/bin/env bats
# Mocked end-to-end test for update_openspec_skills.bash. The script edits
# the tree at REPO_ROOT, so each test points it at a fixture. openspec and
# npm are mocked; nothing touches the network or the real skills.

load '../../lib/testing.sh'

SCRIPT="$BATS_TEST_DIRNAME/../update_openspec_skills.bash"

setup() {
    mock_setup
    FIXTURE="$BATS_TEST_TMPDIR/repo"
    rm -rf "$FIXTURE"
    mkdir -p "$FIXTURE/scripts/lib/npm-tools" "$FIXTURE/.agents/skills/openspec-propose" "$FIXTURE/.agents/skills/openspec-explore"
    cp "$BATS_TEST_DIRNAME/../../lib/npm_tools.sh" "$FIXTURE/scripts/lib/npm_tools.sh"
    printf 'OPENSPEC_VERSION="9.9.9"\nRENOVATE_VERSION="8.8.8"\n' >"$FIXTURE/scripts/lib/versions.sh"
    printf '{"lock": true}\n' >"$FIXTURE/scripts/lib/npm-tools/package-lock.json"
    write_stamp openspec-propose "1.2.3"
    write_stamp openspec-explore "1.2.3"
    export REPO_ROOT="$FIXTURE"
    # Fake openspec: --version prints the pin, update rewrites every stamp
    # and records the directory it ran in.
    mock_command openspec '
if [ "$1" = "--version" ]; then echo 9.9.9; exit 0; fi
echo "$PWD" >"'"$BATS_TEST_TMPDIR"'/update.cwd"
for f in "$PWD"/.agents/skills/openspec-*/SKILL.md; do
    printf -- "---\nmetadata:\n  generatedBy: \"9.9.9\"\n---\n" >"$f"
done
'
}

teardown() {
    mock_teardown
}

write_stamp() {
    printf -- '---\nmetadata:\n  generatedBy: "%s"\n---\n' "$2" >"$FIXTURE/.agents/skills/$1/SKILL.md"
}

@test "runs openspec update in the repo when a stamp is stale, and every stamp ends at the pin" {
    export OPENSPEC_BIN="$MOCK_BIN_DIR/openspec"
    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [ "$(cat "$BATS_TEST_TMPDIR/update.cwd")" = "$FIXTURE" ]
    grep -qF 'generatedBy: "9.9.9"' "$FIXTURE/.agents/skills/openspec-propose/SKILL.md"
    grep -qF 'generatedBy: "9.9.9"' "$FIXTURE/.agents/skills/openspec-explore/SKILL.md"
}

@test "does nothing and never calls openspec or npm when every stamp already matches" {
    write_stamp openspec-propose "9.9.9"
    write_stamp openspec-explore "9.9.9"
    mock_command openspec 'echo "openspec should not run" >&2; exit 99'
    mock_command npm 'echo "npm should not run" >&2; exit 99'
    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"already match 9.9.9"* ]]
}

@test "treats a skill with no stamp as stale" {
    printf -- '---\nname: x\n---\n' >"$FIXTURE/.agents/skills/openspec-explore/SKILL.md"
    write_stamp openspec-propose "9.9.9"
    export OPENSPEC_BIN="$MOCK_BIN_DIR/openspec"
    run "$SCRIPT"
    [ "$status" -eq 0 ]
    grep -qF 'generatedBy: "9.9.9"' "$FIXTURE/.agents/skills/openspec-explore/SKILL.md"
}

@test "installs the pinned openspec from the lockfile with npm ci --ignore-scripts when OPENSPEC_BIN is unset" {
    mock_command npm '
echo "$*" >"'"$BATS_TEST_TMPDIR"'/npm.args"
cp package.json "'"$BATS_TEST_TMPDIR"'/seen-package.json"
cp package-lock.json "'"$BATS_TEST_TMPDIR"'/seen-lock.json"
mkdir -p node_modules/.bin
cp "'"$MOCK_BIN_DIR"'/openspec" node_modules/.bin/openspec
'
    export NPM_BIN="$MOCK_BIN_DIR/npm"
    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$(cat "$BATS_TEST_TMPDIR/npm.args")" == "ci --ignore-scripts"* ]]
    grep -qF '"@fission-ai/openspec": "9.9.9"' "$BATS_TEST_TMPDIR/seen-package.json"
    [ "$(cat "$BATS_TEST_TMPDIR/seen-lock.json")" = '{"lock": true}' ]
    grep -qF 'generatedBy: "9.9.9"' "$FIXTURE/.agents/skills/openspec-propose/SKILL.md"
}

@test "fails when the installed openspec is not the pinned version" {
    mock_command openspec 'if [ "$1" = "--version" ]; then echo 1.0.0; exit 0; fi; exit 99'
    export OPENSPEC_BIN="$MOCK_BIN_DIR/openspec"
    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"openspec is 1.0.0, OPENSPEC_VERSION is 9.9.9"* ]]
}

@test "fails when openspec update leaves a skill without the pinned stamp" {
    mock_command openspec 'if [ "$1" = "--version" ]; then echo 9.9.9; exit 0; fi; exit 0'
    export OPENSPEC_BIN="$MOCK_BIN_DIR/openspec"
    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"left these skills without a 9.9.9 stamp"* ]]
}

@test "fails when the lockfile is missing and no openspec binary is given" {
    rm "$FIXTURE/scripts/lib/npm-tools/package-lock.json"
    mock_command npm 'exit 99'
    export NPM_BIN="$MOCK_BIN_DIR/npm"
    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"package-lock.json is missing"* ]]
}

@test "exits 0 without calling anything when there are no OpenSpec skills" {
    rm -rf "$FIXTURE/.agents/skills"
    mock_command openspec 'exit 99'
    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"nothing to update"* ]]
}
