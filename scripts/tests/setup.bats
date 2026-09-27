#!/usr/bin/env bats
# Mocked end-to-end test for scripts/setup.sh: uses the fixture-copy trick
# (copy setup.sh plus the lib files it sources into a throwaway
# $BATS_TEST_TMPDIR/repo tree, so its own SCRIPT_DIR/REPO_ROOT computation
# resolves there instead of the real repo) combined with real,
# locally-built tarball/script fixtures for `curl` to serve - this
# exercises setup.sh's own orchestration (what it fetches, what it does
# with each fetch, its skip-when-already-installed logic) against real
# tar/install/mv behavior, without ever touching the real network or the
# real repo's actual .tools/.

load '../lib/testing.sh'

REAL_SCRIPTS_DIR="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"

setup() {
    mock_setup

    # shellcheck disable=SC1091
    source "$REAL_SCRIPTS_DIR/lib/versions.sh"

    FIXTURE_ROOT="$BATS_TEST_TMPDIR/repo"
    ASSETS="$BATS_TEST_TMPDIR/assets"
    CURL_LOG="$BATS_TEST_TMPDIR/curl.log"
    mkdir -p "$FIXTURE_ROOT/scripts/lib" "$ASSETS"
    : >"$CURL_LOG"

    cp "$REAL_SCRIPTS_DIR/setup.sh" "$FIXTURE_ROOT/scripts/setup.sh"
    cp "$REAL_SCRIPTS_DIR/lib/versions.sh" "$REAL_SCRIPTS_DIR/lib/fetch.sh" "$REAL_SCRIPTS_DIR/lib/platform.sh" "$FIXTURE_ROOT/scripts/lib/"
    chmod +x "$FIXTURE_ROOT/scripts/setup.sh"

    build_fixture_assets
    install_curl_mock
}

teardown() {
    mock_teardown
}

# Builds real, valid installer artifacts (tarballs via the real `tar`, and
# plain scripts) for every tool setup.sh fetches, so the real tar/install/
# mv commands inside setup.sh work against them unmodified - only the
# network fetch itself (`curl`) is mocked.
build_fixture_assets() {
    # task: a fake installer matching the real taskfile.dev/install.sh
    # interface (`sh -s -- -b BIN_DIR VERSION`).
    cat >"$ASSETS/task-install.sh" <<'EOF'
#!/bin/sh
bindir=""
version=""
while [ $# -gt 0 ]; do
    case "$1" in
        -b)
            bindir="$2"
            shift 2
            ;;
        *)
            version="$1"
            shift
            ;;
    esac
done
mkdir -p "$bindir"
printf '#!/usr/bin/env bash\necho "%s"\n' "${version#v}" >"$bindir/task"
chmod +x "$bindir/task"
EOF

    # actionlint / shellcheck: tar.gz containing an executable script
    # printing the pinned version, matching each tool's own real archive
    # layout (actionlint: file at archive root; shellcheck: nested in a
    # shellcheck-vVERSION/ directory).
    mkdir -p "$ASSETS/actionlint-src"
    printf '#!/usr/bin/env bash\necho "%s"\n' "$ACTIONLINT_VERSION" >"$ASSETS/actionlint-src/actionlint"
    chmod +x "$ASSETS/actionlint-src/actionlint"
    tar -czf "$ASSETS/actionlint.tar.gz" -C "$ASSETS/actionlint-src" actionlint

    mkdir -p "$ASSETS/shellcheck-src/shellcheck-v${SHELLCHECK_VERSION}"
    printf '#!/usr/bin/env bash\necho "version: %s"\n' "$SHELLCHECK_VERSION" \
        >"$ASSETS/shellcheck-src/shellcheck-v${SHELLCHECK_VERSION}/shellcheck"
    chmod +x "$ASSETS/shellcheck-src/shellcheck-v${SHELLCHECK_VERSION}/shellcheck"
    tar -czf "$ASSETS/shellcheck.tar.gz" -C "$ASSETS/shellcheck-src" "shellcheck-v${SHELLCHECK_VERSION}"

    # shfmt: fetched as a single raw binary written directly to a file, no
    # tarball involved.
    printf '#!/usr/bin/env bash\necho "v%s"\n' "$SHFMT_VERSION" >"$ASSETS/shfmt"
    chmod +x "$ASSETS/shfmt"

    # node: tar.gz containing node-vVERSION-OS-ARCH/bin/{node,npm} - the
    # directory name must match exactly what setup.sh itself computes at
    # runtime (real OS/arch, via the same platform.sh this test also
    # copies into the fixture), since it `mv`s that exact path.
    # shellcheck disable=SC1091
    source "$REAL_SCRIPTS_DIR/lib/platform.sh"
    node_dirname="node-v${NODE_VERSION}-$(detect_os)-$(detect_arch_node)"
    mkdir -p "$ASSETS/node-src/$node_dirname/bin"
    printf '#!/usr/bin/env bash\necho "v%s"\n' "$NODE_VERSION" >"$ASSETS/node-src/$node_dirname/bin/node"
    chmod +x "$ASSETS/node-src/$node_dirname/bin/node"
    # setup.sh calls "$NODE_DIR/bin/npm" by its full path (not "npm"
    # resolved via PATH), so this fake npm - not a mock_command stub - is
    # the one that actually runs for the openspec install step below. It
    # simulates npm's real side effect (dropping an executable at
    # --prefix/bin/openspec) rather than actually installing anything.
    cat >"$ASSETS/node-src/$node_dirname/bin/npm" <<EOF
#!/usr/bin/env bash
echo "\$*" >> "$BATS_TEST_TMPDIR/npm.log"
prefix=""
prev=""
for arg in "\$@"; do
    [ "\$prev" = "--prefix" ] && prefix="\$arg"
    prev="\$arg"
done
mkdir -p "\$prefix/bin"
printf '#!/usr/bin/env bash\necho "$OPENSPEC_VERSION"\n' > "\$prefix/bin/openspec"
chmod +x "\$prefix/bin/openspec"
EOF
    chmod +x "$ASSETS/node-src/$node_dirname/bin/npm"
    tar -czf "$ASSETS/node.tar.gz" -C "$ASSETS/node-src" "$node_dirname"

    # bats-core: tar.gz containing bats-core-VERSION/install.sh, matching
    # the real upstream project's own install.sh interface
    # (`install.sh <prefix>`, creating <prefix>/bin/bats).
    mkdir -p "$ASSETS/bats-src/bats-core-${BATS_VERSION}"
    cat >"$ASSETS/bats-src/bats-core-${BATS_VERSION}/install.sh" <<EOF
#!/bin/sh
prefix="\$1"
mkdir -p "\$prefix/bin"
printf '#!/usr/bin/env bash\necho "Bats %s"\n' "$BATS_VERSION" >"\$prefix/bin/bats"
chmod +x "\$prefix/bin/bats"
EOF
    chmod +x "$ASSETS/bats-src/bats-core-${BATS_VERSION}/install.sh"
    tar -czf "$ASSETS/bats-core.tar.gz" -C "$ASSETS/bats-src" "bats-core-${BATS_VERSION}"
}

# Mocks curl (fetch.sh's FETCH prefers curl when present, and this dev
# machine has a real one, so mocking curl - not wget - is what actually
# takes effect) to serve the fixture assets built above, keyed by a
# distinctive substring of each tool's real download URL, and to log
# every URL it was asked to fetch so a test can assert a skipped tool's
# URL was never requested.
install_curl_mock() {
    mock_command curl "
echo \"\$*\" >> '$CURL_LOG'
url=\"\${*: -1}\"
case \"\$url\" in
    *taskfile.dev*) cat '$ASSETS/task-install.sh' ;;
    *actionlint*) cat '$ASSETS/actionlint.tar.gz' ;;
    *shellcheck*) cat '$ASSETS/shellcheck.tar.gz' ;;
    *mvdan/sh*) cat '$ASSETS/shfmt' ;;
    *bats-core*) cat '$ASSETS/bats-core.tar.gz' ;;
    *nodejs.org*) cat '$ASSETS/node.tar.gz' ;;
    *) echo \"mock curl: unexpected URL: \$url\" >&2; exit 1 ;;
esac
"
}

# Seeds every tool as already installed at the pinned version, except for
# any tool name passed as an argument - those are left absent so the
# script attempts a fresh install for exactly them.
seed_all_installed_except() {
    local skip=" $* "
    local bin="$FIXTURE_ROOT/.tools/bin"
    local node_dir="$FIXTURE_ROOT/.tools/node"
    local bats_dir="$FIXTURE_ROOT/.tools/bats"
    mkdir -p "$bin"

    [[ "$skip" == *" task "* ]] || {
        printf '#!/usr/bin/env bash\necho "%s"\n' "${TASK_VERSION#v}" >"$bin/task"
        chmod +x "$bin/task"
    }
    [[ "$skip" == *" actionlint "* ]] || {
        printf '#!/usr/bin/env bash\necho "%s"\n' "$ACTIONLINT_VERSION" >"$bin/actionlint"
        chmod +x "$bin/actionlint"
    }
    [[ "$skip" == *" shellcheck "* ]] || {
        printf '#!/usr/bin/env bash\necho "version: %s"\n' "$SHELLCHECK_VERSION" >"$bin/shellcheck"
        chmod +x "$bin/shellcheck"
    }
    [[ "$skip" == *" shfmt "* ]] || {
        printf '#!/usr/bin/env bash\necho "v%s"\n' "$SHFMT_VERSION" >"$bin/shfmt"
        chmod +x "$bin/shfmt"
    }
    [[ "$skip" == *" bats "* ]] || {
        mkdir -p "$bats_dir/bin"
        printf '#!/usr/bin/env bash\necho "Bats %s"\n' "$BATS_VERSION" >"$bats_dir/bin/bats"
        chmod +x "$bats_dir/bin/bats"
    }
    [[ "$skip" == *" node "* ]] || {
        mkdir -p "$node_dir/bin"
        printf '#!/usr/bin/env bash\necho "v%s"\n' "$NODE_VERSION" >"$node_dir/bin/node"
        chmod +x "$node_dir/bin/node"
        printf '#!/usr/bin/env bash\necho "npm should not run"\n' >"$node_dir/bin/npm"
        chmod +x "$node_dir/bin/npm"
    }
    [[ "$skip" == *" openspec "* ]] || {
        printf '#!/usr/bin/env bash\necho "%s"\n' "$OPENSPEC_VERSION" >"$bin/openspec"
        chmod +x "$bin/openspec"
    }
}

@test "fresh clone: task setup installs every pinned tool from scratch" {
    run "$FIXTURE_ROOT/scripts/setup.sh"
    [ "$status" -eq 0 ]

    [ -x "$FIXTURE_ROOT/.tools/bin/task" ]
    [ "$("$FIXTURE_ROOT/.tools/bin/task" --version)" = "${TASK_VERSION#v}" ]

    [ -x "$FIXTURE_ROOT/.tools/bin/actionlint" ]
    [ "$("$FIXTURE_ROOT/.tools/bin/actionlint" -version)" = "$ACTIONLINT_VERSION" ]

    [ -x "$FIXTURE_ROOT/.tools/bin/shellcheck" ]
    [ "$("$FIXTURE_ROOT/.tools/bin/shellcheck" --version)" = "version: $SHELLCHECK_VERSION" ]

    [ -x "$FIXTURE_ROOT/.tools/bin/shfmt" ]
    [ "$("$FIXTURE_ROOT/.tools/bin/shfmt" --version)" = "v$SHFMT_VERSION" ]

    [ -x "$FIXTURE_ROOT/.tools/bats/bin/bats" ]
    [ "$("$FIXTURE_ROOT/.tools/bats/bin/bats" --version)" = "Bats $BATS_VERSION" ]

    [ -x "$FIXTURE_ROOT/.tools/node/bin/node" ]
    [ "$("$FIXTURE_ROOT/.tools/node/bin/node" --version)" = "v$NODE_VERSION" ]

    [ -x "$FIXTURE_ROOT/.tools/bin/openspec" ]
    [ "$("$FIXTURE_ROOT/.tools/bin/openspec" --version)" = "$OPENSPEC_VERSION" ]

    grep -q "taskfile.dev/install.sh" "$CURL_LOG"
    grep -q "nodejs.org" "$CURL_LOG"
    grep -q -- "--prefix $FIXTURE_ROOT/.tools" "$BATS_TEST_TMPDIR/npm.log"
}

@test "already installed at the pinned version: skips every fetch" {
    seed_all_installed_except
    run "$FIXTURE_ROOT/scripts/setup.sh"
    [ "$status" -eq 0 ]

    [[ "$output" == *"task: already installed"* ]]
    [[ "$output" == *"actionlint: already installed"* ]]
    [[ "$output" == *"shellcheck: already installed"* ]]
    [[ "$output" == *"shfmt: already installed"* ]]
    [[ "$output" == *"bats: already installed"* ]]
    [[ "$output" == *"node: already installed"* ]]
    [[ "$output" == *"openspec: already installed"* ]]

    [ ! -s "$CURL_LOG" ]
    [ ! -f "$BATS_TEST_TMPDIR/npm.log" ]
}

@test "a version-mismatched tool is reinstalled while others are left alone" {
    seed_all_installed_except shfmt
    # Corrupt shfmt's own reported version so it looks stale.
    printf '#!/usr/bin/env bash\necho "v0.0.1"\n' >"$FIXTURE_ROOT/.tools/bin/shfmt"
    chmod +x "$FIXTURE_ROOT/.tools/bin/shfmt"

    run "$FIXTURE_ROOT/scripts/setup.sh"
    [ "$status" -eq 0 ]

    [[ "$output" == *"shfmt: installing $SHFMT_VERSION"* ]]
    [ "$("$FIXTURE_ROOT/.tools/bin/shfmt" --version)" = "v$SHFMT_VERSION" ]

    [[ "$output" == *"task: already installed"* ]]
    [[ "$output" == *"actionlint: already installed"* ]]
    [ ! -f "$BATS_TEST_TMPDIR/npm.log" ]
}
