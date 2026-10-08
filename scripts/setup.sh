#!/usr/bin/env bash
# Bootstraps this repo's toolchain into .tools/, entirely local to the
# repo: never touches the user's global PATH, shell profile, or home
# directory.
#
# Deliberately a plain script, not a Taskfile task: `task` itself may not
# exist yet on a fresh clone, so bootstrapping it *through* the Taskfile
# would be circular. Local devs run:
#   ./scripts/setup.sh
#   source scripts/env.sh   # put .tools/bin, .tools/node/bin, and .tools/bats/bin on PATH for this shell session
#
# Tools install in dependency order (node before the npm-installed
# openspec and renovate), not alphabetically; the pins in
# scripts/lib/versions.sh are the alphabetical list.
#
# CI (see checks.yaml and ci-gate.yaml) passes --lint-only: neither
# required workflow runs openspec or renovate, so CI skips the
# node/openspec/renovate install and only bootstraps the lint binaries
# (task, actionlint, shellcheck, shfmt) plus bats (needed by the bash test
# suite, which does run under --lint-only) and uv (needed by the uv.lock
# sync check).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BIN_DIR="$REPO_ROOT/.tools/bin"
NODE_DIR="$REPO_ROOT/.tools/node"
BATS_DIR="$REPO_ROOT/.tools/bats"

LINT_ONLY=0
if [[ "${1:-}" == "--lint-only" ]]; then
    LINT_ONLY=1
fi

# shellcheck source=scripts/lib/versions.sh
source "$SCRIPT_DIR/lib/versions.sh"
# shellcheck source=scripts/lib/fetch.sh
source "$SCRIPT_DIR/lib/fetch.sh"
# shellcheck source=scripts/lib/platform.sh
source "$SCRIPT_DIR/lib/platform.sh"

# setup.sh's own job is to fetch installers, so it needs a fetcher itself;
# ensure_fetcher (scripts/lib/fetch.sh) installs curl via a detected package
# manager if neither curl nor wget is already present, or fails with
# instructions if it can't.
ensure_fetcher

mkdir -p "$BIN_DIR"

# Compares two version strings, ignoring a leading 'v' on either side (some
# tools print one, some don't, and the pins in lib/versions.sh aren't
# consistent either) - so bumping a pin there is what actually decides
# whether a tool gets reinstalled below, not just whether a binary happens
# to already exist.
version_matches() {
    [ "${1#v}" = "${2#v}" ]
}

OS="$(detect_os)"
ARCH_GNU="$(detect_arch_gnu)"
ARCH_SC="$(detect_arch_shellcheck)"

if [ -x "$BIN_DIR/task" ] && version_matches "$("$BIN_DIR/task" --version)" "$TASK_VERSION"; then
    echo "task: already installed ($("$BIN_DIR/task" --version))"
else
    echo "task: installing $TASK_VERSION into $BIN_DIR ..."
    TMP_DIR="$(mktemp -d)"
    FETCH "https://github.com/go-task/task/releases/download/${TASK_VERSION}/task_${OS}_${ARCH_GNU}.tar.gz" >"$TMP_DIR/task.tar.gz"
    tar -xzf "$TMP_DIR/task.tar.gz" -C "$TMP_DIR" task
    install "$TMP_DIR/task" "$BIN_DIR/task"
    rm -rf "$TMP_DIR"
    echo "task: installed ($("$BIN_DIR/task" --version))"
fi

if [ -x "$BIN_DIR/actionlint" ] && version_matches "$("$BIN_DIR/actionlint" -version | head -n 1)" "$ACTIONLINT_VERSION"; then
    echo "actionlint: already installed ($("$BIN_DIR/actionlint" -version | head -n 1))"
else
    echo "actionlint: installing $ACTIONLINT_VERSION into $BIN_DIR ..."
    TMP_DIR="$(mktemp -d)"
    FETCH "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_${OS}_${ARCH_GNU}.tar.gz" >"$TMP_DIR/actionlint.tar.gz"
    tar -xzf "$TMP_DIR/actionlint.tar.gz" -C "$TMP_DIR" actionlint
    install "$TMP_DIR/actionlint" "$BIN_DIR/actionlint"
    rm -rf "$TMP_DIR"
    echo "actionlint: installed ($("$BIN_DIR/actionlint" -version | head -n 1))"
fi

if [ -x "$BIN_DIR/shellcheck" ] && version_matches "$("$BIN_DIR/shellcheck" --version | awk -F': ' '/^version:/{print $2}')" "$SHELLCHECK_VERSION"; then
    echo "shellcheck: already installed ($("$BIN_DIR/shellcheck" --version | grep '^version:'))"
else
    echo "shellcheck: installing $SHELLCHECK_VERSION into $BIN_DIR ..."
    TMP_DIR="$(mktemp -d)"
    FETCH "https://github.com/koalaman/shellcheck/releases/download/v${SHELLCHECK_VERSION}/shellcheck-v${SHELLCHECK_VERSION}.${OS}.${ARCH_SC}.tar.gz" >"$TMP_DIR/shellcheck.tar.gz"
    tar -xzf "$TMP_DIR/shellcheck.tar.gz" -C "$TMP_DIR"
    install "$TMP_DIR/shellcheck-v${SHELLCHECK_VERSION}/shellcheck" "$BIN_DIR/shellcheck"
    rm -rf "$TMP_DIR"
    echo "shellcheck: installed ($("$BIN_DIR/shellcheck" --version | grep '^version:'))"
fi

if [ -x "$BIN_DIR/shfmt" ] && version_matches "$("$BIN_DIR/shfmt" --version)" "$SHFMT_VERSION"; then
    echo "shfmt: already installed ($("$BIN_DIR/shfmt" --version))"
else
    echo "shfmt: installing $SHFMT_VERSION into $BIN_DIR ..."
    FETCH "https://github.com/mvdan/sh/releases/download/v${SHFMT_VERSION}/shfmt_v${SHFMT_VERSION}_${OS}_${ARCH_GNU}" >"$BIN_DIR/shfmt"
    chmod +x "$BIN_DIR/shfmt"
    echo "shfmt: installed ($("$BIN_DIR/shfmt" --version))"
fi

# uv ships as a tar.gz holding uv-<triple>/uv (plus uvx). Installed
# unconditionally (not gated behind --lint-only): `uv lock --check`, run by
# check_uv_locks.bash, is one of the standing checks in check_all.bash.
if [ -x "$BIN_DIR/uv" ] && version_matches "$("$BIN_DIR/uv" --version | awk '{print $2}')" "$UV_VERSION"; then
    echo "uv: already installed ($("$BIN_DIR/uv" --version))"
else
    echo "uv: installing $UV_VERSION into $BIN_DIR ..."
    TRIPLE_UV="$(detect_triple_uv)"
    TMP_DIR="$(mktemp -d)"
    FETCH "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-${TRIPLE_UV}.tar.gz" >"$TMP_DIR/uv.tar.gz"
    tar -xzf "$TMP_DIR/uv.tar.gz" -C "$TMP_DIR"
    install "$TMP_DIR/uv-${TRIPLE_UV}/uv" "$BIN_DIR/uv"
    rm -rf "$TMP_DIR"
    echo "uv: installed ($("$BIN_DIR/uv" --version))"
fi

# bats-core ships as a bin/+libexec/+lib/ tree, not a single relocatable
# binary (its own install.sh always creates all three under whatever
# prefix it's given) - so like node below, it gets its own .tools/bats/
# directory instead of joining the flat .tools/bin/, and scripts/env.sh
# puts .tools/bats/bin on PATH alongside it. Installed straight from its
# own GitHub source tarball, deliberately not through npm/node: it's a
# pure bash tool with no actual Node dependency, and the only reason it
# would otherwise need node bootstrapped first is npm being a convenient
# but unnecessary distribution channel for it. Installed unconditionally
# (not gated behind --lint-only): the bash test suite it runs is one of
# the standing checks in check_all.bash, which CI's --lint-only bootstrap
# still needs to pass.
if [ -x "$BATS_DIR/bin/bats" ] && version_matches "$("$BATS_DIR/bin/bats" --version | awk '{print $2}')" "$BATS_VERSION"; then
    echo "bats: already installed ($("$BATS_DIR/bin/bats" --version))"
else
    echo "bats: installing $BATS_VERSION into $BATS_DIR ..."
    TMP_DIR="$(mktemp -d)"
    FETCH "https://github.com/bats-core/bats-core/archive/refs/tags/v${BATS_VERSION}.tar.gz" >"$TMP_DIR/bats-core.tar.gz"
    tar -xzf "$TMP_DIR/bats-core.tar.gz" -C "$TMP_DIR"
    rm -rf "$BATS_DIR"
    "$TMP_DIR/bats-core-${BATS_VERSION}/install.sh" "$BATS_DIR"
    rm -rf "$TMP_DIR"
    echo "bats: installed ($("$BATS_DIR/bin/bats" --version))"
fi

if [ "$LINT_ONLY" -eq 0 ]; then
    # node ships as a whole bin/+lib/ tree (npm/npx are symlinks resolved
    # relative to a sibling lib/node_modules/npm/, not a single relocatable
    # binary like every other tool above) -- so it gets its own .tools/node/
    # directory instead of joining the flat .tools/bin/, and scripts/env.sh puts
    # .tools/node/bin on PATH alongside .tools/bin. It exists solely to run
    # openspec below.
    ARCH_NODE="$(detect_arch_node)"

    if [ -x "$NODE_DIR/bin/node" ] && version_matches "$("$NODE_DIR/bin/node" --version)" "$NODE_VERSION"; then
        echo "node: already installed ($("$NODE_DIR/bin/node" --version))"
    else
        echo "node: installing $NODE_VERSION into $NODE_DIR ..."
        TMP_DIR="$(mktemp -d)"
        FETCH "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-${OS}-${ARCH_NODE}.tar.gz" >"$TMP_DIR/node.tar.gz"
        tar -xzf "$TMP_DIR/node.tar.gz" -C "$TMP_DIR"
        rm -rf "$NODE_DIR"
        mv "$TMP_DIR/node-v${NODE_VERSION}-${OS}-${ARCH_NODE}" "$NODE_DIR"
        rm -rf "$TMP_DIR"
        echo "node: installed ($("$NODE_DIR/bin/node" --version))"
    fi

    # Put the freshly bootstrapped node/npm on PATH for the rest of this script:
    # openspec's own shim below has a `#!/usr/bin/env node` shebang, and npm
    # itself may shell out to `node` by name -- neither can rely on a `node`
    # that's only ever added to PATH later by scripts/env.sh in the user's own
    # shell.
    export PATH="$NODE_DIR/bin:$PATH"

    if [ -x "$BIN_DIR/openspec" ] && version_matches "$("$BIN_DIR/openspec" --version)" "$OPENSPEC_VERSION"; then
        echo "openspec: already installed ($("$BIN_DIR/openspec" --version))"
    else
        echo "openspec: installing $OPENSPEC_VERSION into $BIN_DIR ..."
        # --userconfig/--cache keep npm entirely inside .tools/: without them
        # npm still reads $HOME/.npmrc and writes its cache under $HOME,
        # despite --prefix pointing at .tools.
        "$NODE_DIR/bin/npm" install --global --prefix "$REPO_ROOT/.tools" \
            --userconfig="$REPO_ROOT/.tools/.npmrc" \
            --cache="$REPO_ROOT/.tools/.npm-cache" \
            "@fission-ai/openspec@${OPENSPEC_VERSION}"
        echo "openspec: installed ($("$BIN_DIR/openspec" --version))"
    fi

    if [ -x "$BIN_DIR/renovate" ] && version_matches "$("$BIN_DIR/renovate" --version)" "$RENOVATE_VERSION"; then
        echo "renovate: already installed ($("$BIN_DIR/renovate" --version))"
    else
        echo "renovate: installing $RENOVATE_VERSION into $BIN_DIR ..."
        # --userconfig/--cache keep npm entirely inside .tools/: without them
        # npm still reads $HOME/.npmrc and writes its cache under $HOME,
        # despite --prefix pointing at .tools.
        "$NODE_DIR/bin/npm" install --global --prefix "$REPO_ROOT/.tools" \
            --userconfig="$REPO_ROOT/.tools/.npmrc" \
            --cache="$REPO_ROOT/.tools/.npm-cache" \
            "renovate@${RENOVATE_VERSION}"
        echo "renovate: installed ($("$BIN_DIR/renovate" --version))"
    fi
else
    echo "node/openspec/renovate: skipped (--lint-only)"
fi

echo
echo "Setup complete. Run 'source scripts/env.sh' to put .tools/bin, .tools/node/bin, and .tools/bats/bin on PATH, then 'task shell:lint'."
