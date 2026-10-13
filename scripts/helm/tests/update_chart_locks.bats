#!/usr/bin/env bats
# Mocked end-to-end test for update_chart_locks.bash: the script computes
# its own REPO_ROOT from BASH_SOURCE and prefers $REPO_ROOT/.tools/bin/helm,
# so the fixture holds a copy of the script plus a fake helm that records
# its arguments and mimics the real side effects (a Chart.lock next to
# Chart.yaml, and a charts/ directory of downloaded subcharts).

load '../../lib/testing.sh'

FIXTURE_REPO="$BATS_TEST_TMPDIR/repo"

setup() {
    mkdir -p "$FIXTURE_REPO/scripts/helm" "$FIXTURE_REPO/.tools/bin"
    cp "$BATS_TEST_DIRNAME/../update_chart_locks.bash" "$FIXTURE_REPO/scripts/helm/update_chart_locks.bash"
    chmod +x "$FIXTURE_REPO/scripts/helm/update_chart_locks.bash"
    SCRIPT="$FIXTURE_REPO/scripts/helm/update_chart_locks.bash"

    cat >"$FIXTURE_REPO/.tools/bin/helm" <<EOS
#!/usr/bin/env bash
echo "\$* (cache=\$HELM_CACHE_HOME)" >> "$BATS_TEST_TMPDIR/helm.log"
[ "\$1 \$2" = "dependency update" ] || exit 64
chart_dir="\$3"
grep -q BROKEN "\$chart_dir/Chart.yaml" && { echo "Error: can't get a valid version"; exit 1; }
mkdir -p "\$chart_dir/charts"
echo "digest: fake" > "\$chart_dir/Chart.lock"
exit 0
EOS
    chmod +x "$FIXTURE_REPO/.tools/bin/helm"
}

add_chart() {
    local dir="$1" body="${2:-}"
    mkdir -p "$FIXTURE_REPO/$dir"
    printf 'apiVersion: v2\nname: x\nversion: 0.1.0\n%s\n' "$body" >"$FIXTURE_REPO/$dir/Chart.yaml"
}

@test "updates every chart that declares dependencies and removes the downloaded charts/ dir" {
    add_chart app/helm/umbrella $'dependencies:\n  - name: a\n    version: "1"\n    repository: "file://../a"'
    add_chart app/helm/a

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK: updated Chart.lock for 1 chart(s)"* ]]
    [ -f "$FIXTURE_REPO/app/helm/umbrella/Chart.lock" ]
    [ ! -e "$FIXTURE_REPO/app/helm/umbrella/charts" ]
    # A chart without dependencies is left alone.
    [ ! -e "$FIXTURE_REPO/app/helm/a/Chart.lock" ]
    [ "$(wc -l <"$BATS_TEST_TMPDIR/helm.log")" -eq 1 ]
}

@test "a charts/ dir that existed before the run is left in place" {
    add_chart app/helm/umbrella $'dependencies:\n  - name: a'
    mkdir -p "$FIXTURE_REPO/app/helm/umbrella/charts"

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [ -d "$FIXTURE_REPO/app/helm/umbrella/charts" ]
}

@test "helm's own cache lives under .tools/helm unless the caller set one" {
    add_chart app/helm/umbrella $'dependencies:\n  - name: a'

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    grep -q "cache=$FIXTURE_REPO/.tools/helm/cache" "$BATS_TEST_TMPDIR/helm.log"

    HELM_CACHE_HOME="$BATS_TEST_TMPDIR/own-cache" run "$SCRIPT"
    [ "$status" -eq 0 ]
    grep -q "cache=$BATS_TEST_TMPDIR/own-cache" "$BATS_TEST_TMPDIR/helm.log"
}

@test "an explicit root directory is updated instead of the repo root" {
    add_chart app/helm/umbrella $'dependencies:\n  - name: a'
    mkdir -p "$BATS_TEST_TMPDIR/other/helm/u"
    printf 'name: u\nversion: 1.0.0\ndependencies:\n  - name: a\n' >"$BATS_TEST_TMPDIR/other/helm/u/Chart.yaml"

    run "$SCRIPT" "$BATS_TEST_TMPDIR/other"
    [ "$status" -eq 0 ]
    [ -f "$BATS_TEST_TMPDIR/other/helm/u/Chart.lock" ]
    [ ! -e "$FIXTURE_REPO/app/helm/umbrella/Chart.lock" ]
}

@test "a failing helm dependency update fails the run but still tries the other charts" {
    add_chart app/helm/a-broken $'BROKEN\ndependencies:\n  - name: a'
    add_chart app/helm/b-fine $'dependencies:\n  - name: a'

    run "$SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"helm dependency update failed in"*"a-broken"* ]]
    [ -f "$FIXTURE_REPO/app/helm/b-fine/Chart.lock" ]
}

@test "extra arguments -> usage error" {
    run "$SCRIPT" one two
    [ "$status" -eq 2 ]
    [[ "$output" == *"Usage:"* ]]
}

@test "helm missing from both .tools/bin and PATH -> exit 2 with setup hint" {
    rm "$FIXTURE_REPO/.tools/bin/helm"
    PATH="/usr/bin:/bin" run "$SCRIPT"
    [ "$status" -eq 2 ]
    [[ "$output" == *"helm not found"* ]]
}
