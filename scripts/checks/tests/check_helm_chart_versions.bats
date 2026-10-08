#!/usr/bin/env bats
# Mocked end-to-end test for check_helm_chart_versions.bash: real git
# commands are exercised against a throwaway git repository (path-scoped
# log history and commit ancestry are this script's whole job - mocking
# git out would leave nothing real to test). The script itself is copied
# alongside a scripts/checks/ subtree so its own SCRIPT_DIR/REPO_ROOT
# resolution (two levels up) lines up with the fixture repo's root.

SCRIPT_UNDER_TEST="$BATS_TEST_DIRNAME/../check_helm_chart_versions.bash"

setup() {
    REPO_DIR="$BATS_TEST_TMPDIR/repo"
    mkdir -p "$REPO_DIR/scripts/checks"
    cp "$SCRIPT_UNDER_TEST" "$REPO_DIR/scripts/checks/check_helm_chart_versions.bash"
    chmod +x "$REPO_DIR/scripts/checks/check_helm_chart_versions.bash"
    cd "$REPO_DIR" || exit 1
    git init -q .
    git config user.email "test@example.com"
    git config user.name "Test User"
    # Override any global tag.gpgSign/tag.forceSignAnnotated (some
    # contributors' machines set these) so a plain `git tag <name>` stays
    # a lightweight tag, not one that needs a GPG key to create.
    git config tag.gpgSign false
    git config tag.forceSignAnnotated false
}

run_check() {
    run ./scripts/checks/check_helm_chart_versions.bash "$@"
}

# Writes a minimal chart at $1 with Chart.yaml `version:` set to $2.
write_chart() {
    local dir="$1" version="$2"
    mkdir -p "$dir/templates"
    cat >"$dir/Chart.yaml" <<EOF
apiVersion: v2
name: $(basename "$dir")
version: $version
EOF
    echo "kind: ConfigMap" >"$dir/templates/configmap.yaml"
}

@test "passes when a chart's contents changed and its version was bumped afterward" {
    write_chart "chart" "0.1.0"
    git add -A
    git commit -q -m "add chart 0.1.0"

    echo "kind: Deployment" >>chart/templates/configmap.yaml
    git add -A
    git commit -q -m "change chart contents"

    write_chart "chart" "0.1.1"
    git add -A
    git commit -q -m "bump chart version"

    run_check
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: every Helm chart's version reflects its latest content change"* ]]
}

@test "fails, naming the chart, when contents changed with no version bump" {
    write_chart "chart" "0.1.0"
    git add -A
    git commit -q -m "add chart 0.1.0"

    echo "kind: Deployment" >>chart/templates/configmap.yaml
    git add -A
    git commit -q -m "change chart contents, forget to bump"

    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"chart changed but its version was never bumped"* ]]
}

@test "fails when the version bump commit predates the latest content change" {
    write_chart "chart" "0.1.0"
    git add -A
    git commit -q -m "add chart 0.1.0"

    write_chart "chart" "0.1.1"
    git add -A
    git commit -q -m "bump chart version early"

    echo "kind: Deployment" >>chart/templates/configmap.yaml
    git add -A
    git commit -q -m "change chart contents after the bump"

    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"was never bumped since (or was bumped before) that change"* ]]
}

@test "a violation from long before the last release tag is still detected" {
    write_chart "chart" "0.1.0"
    git add -A
    git commit -q -m "add chart 0.1.0"

    # Unbumped content change, older history - the whole point of the
    # tag-free design: nothing since scopes this out.
    echo "kind: Deployment" >>chart/templates/configmap.yaml
    git add -A
    git commit -q -m "change chart contents, forget to bump"
    git tag 0.1.0

    # A later, unrelated release tag with no further chart changes.
    echo "unrelated" >other.txt
    git add -A
    git commit -q -m "unrelated change"
    git tag 0.2.0

    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"chart changed but its version was never bumped"* ]]
}

@test "a chart added for the first time, with its version set in that commit, is not flagged" {
    write_chart "old-chart" "1.0.0"
    git add -A
    git commit -q -m "seed repo"

    write_chart "new-chart" "0.1.0"
    git add -A
    git commit -q -m "add a brand-new chart"

    run_check
    [ "$status" -eq 0 ]
}

@test "passes when nothing has changed a chart's contents" {
    write_chart "chart" "0.1.0"
    git add -A
    git commit -q -m "add chart 0.1.0"

    echo "unrelated" >other.txt
    git add -A
    git commit -q -m "unrelated change"

    run_check
    [ "$status" -eq 0 ]
}

@test "a version bump nested under dependencies: does not count as the chart's own bump" {
    write_chart "chart" "0.1.0"
    git add -A
    git commit -q -m "add chart 0.1.0"

    echo "kind: Deployment" >>chart/templates/configmap.yaml
    cat >>chart/Chart.yaml <<'EOF'
dependencies:
  - name: sub
    version: 9.9.9
EOF
    git add -A
    git commit -q -m "change contents, only bump nested dep version"

    run_check
    [ "$status" -eq 1 ]
}

@test "exits 2 when given an argument" {
    write_chart "chart" "0.1.0"
    git add -A
    git commit -q -m "add chart 0.1.0"

    run_check some-argument
    [ "$status" -eq 2 ]
    [[ "$output" == *"Usage:"* ]]
}
