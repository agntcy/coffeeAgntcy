#!/usr/bin/env bats
# Mocked end-to-end test for check_helm_chart_locks.bash: the fixture is a
# real git repo holding copies of the check and of the update script it
# calls, plus a fake helm whose `dependency update` writes a Chart.lock
# whose digest is a checksum of the chart's Chart.yaml (and a fresh
# `generated:` line, which the check must ignore). Committed locks are
# written with the same function, so editing a Chart.yaml afterwards is how
# a test makes a lock stale.

load '../../lib/testing.sh'

FIXTURE_REPO="$BATS_TEST_TMPDIR/repo"

setup() {
    mkdir -p "$FIXTURE_REPO/scripts/checks" "$FIXTURE_REPO/scripts/helm" "$FIXTURE_REPO/.tools/bin"
    cp "$BATS_TEST_DIRNAME/../check_helm_chart_locks.bash" "$FIXTURE_REPO/scripts/checks/check_helm_chart_locks.bash"
    cp "$BATS_TEST_DIRNAME/../../helm/update_chart_locks.bash" "$FIXTURE_REPO/scripts/helm/update_chart_locks.bash"
    chmod +x "$FIXTURE_REPO/scripts/checks/check_helm_chart_locks.bash" "$FIXTURE_REPO/scripts/helm/update_chart_locks.bash"
    SCRIPT="$FIXTURE_REPO/scripts/checks/check_helm_chart_locks.bash"

    cat >"$FIXTURE_REPO/.tools/bin/helm" <<EOS
#!/usr/bin/env bash
echo "\$PWD \$*" >> "$BATS_TEST_TMPDIR/helm.log"
[ "\$1 \$2" = "dependency update" ] || exit 64
chart_dir="\$3"
grep -q BROKEN "\$chart_dir/Chart.yaml" && { echo "Error: can't get a valid version for 1 subchart(s)"; exit 1; }
printf 'digest: %s\ngenerated: "%s"\n' "\$(cksum <"\$chart_dir/Chart.yaml")" "\$(date +%s%N)" > "\$chart_dir/Chart.lock"
exit 0
EOS
    chmod +x "$FIXTURE_REPO/.tools/bin/helm"

    git -C "$FIXTURE_REPO" init -q
    git -C "$FIXTURE_REPO" config user.email "test@example.com"
    git -C "$FIXTURE_REPO" config user.name "Test"
}

# add_chart <dir> [with-deps]: a chart with a Chart.yaml and, when it has
# dependencies, a matching committed Chart.lock.
add_chart() {
    local dir="$1" deps="${2:-}"
    mkdir -p "$FIXTURE_REPO/$dir"
    printf 'apiVersion: v2\nname: x\nversion: 0.1.0\n' >"$FIXTURE_REPO/$dir/Chart.yaml"
    if [ "$deps" = "with-deps" ]; then
        printf 'dependencies:\n  - name: a\n    version: "1"\n    repository: "file://../a"\n' >>"$FIXTURE_REPO/$dir/Chart.yaml"
        write_lock "$dir"
    fi
}

write_lock() {
    printf 'digest: %s\ngenerated: "committed-long-ago"\n' "$(cksum <"$FIXTURE_REPO/$1/Chart.yaml")" >"$FIXTURE_REPO/$1/Chart.lock"
}

stage() {
    git -C "$FIXTURE_REPO" add -A
}

@test "every lock in sync (generated timestamp ignored) -> OK" {
    add_chart helm/a
    add_chart helm/umbrella with-deps
    stage

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: 1 Chart.lock file(s) in sync"* ]]
}

@test "a Chart.yaml edited without refreshing its lock -> flagged with a diff and the fix command" {
    add_chart helm/a
    add_chart helm/umbrella with-deps
    printf '  - name: b\n' >>"$FIXTURE_REPO/helm/umbrella/Chart.yaml"
    stage

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"helm/umbrella: Chart.lock is out of sync with Chart.yaml"* ]]
    [[ "$output" == *"task helm:update-locks"* ]]
}

@test "a chart with dependencies and no Chart.lock -> flagged" {
    add_chart helm/a
    add_chart helm/umbrella with-deps
    rm "$FIXTURE_REPO/helm/umbrella/Chart.lock"
    stage

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"helm/umbrella: no Chart.lock"* ]]
}

@test "helm dependency update failing (unresolvable sibling) -> explained failure" {
    add_chart helm/a
    add_chart helm/umbrella with-deps
    printf '# BROKEN\n' >>"$FIXTURE_REPO/helm/umbrella/Chart.yaml"
    stage

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"'helm dependency update' failed"* ]]
    [[ "$output" == *"can't get a valid version"* ]]
    [[ "$output" == *"file:// subchart"* ]]
}

@test "the check never touches the committed lock" {
    add_chart helm/a
    add_chart helm/umbrella with-deps
    printf '  - name: b\n' >>"$FIXTURE_REPO/helm/umbrella/Chart.yaml"
    stage
    before="$(cat "$FIXTURE_REPO/helm/umbrella/Chart.lock")"

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [ "$(cat "$FIXTURE_REPO/helm/umbrella/Chart.lock")" = "$before" ]
    [ ! -e "$FIXTURE_REPO/helm/umbrella/charts" ]
}

@test "untracked charts are ignored" {
    add_chart helm/a
    stage
    add_chart helm/untracked with-deps
    printf '  - name: b\n' >>"$FIXTURE_REPO/helm/untracked/Chart.yaml"

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"no Helm chart declares dependencies"* ]]
}

@test "no chart declares dependencies -> OK without calling helm" {
    add_chart helm/a
    stage

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"no Helm chart declares dependencies"* ]]
    [ ! -f "$BATS_TEST_TMPDIR/helm.log" ]
}

@test "extra arguments -> usage error" {
    run "$SCRIPT" extra
    [ "$status" -eq 2 ]
    [[ "$output" == *"Usage:"* ]]
}
