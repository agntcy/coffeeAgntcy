#!/usr/bin/env bash
# Bootstraps this repo's toolchain into .tools/, entirely local to the
# repo: never touches the user's global PATH, shell profile, or home
# directory.
#
# Deliberately a plain script, not a Taskfile task: `task` itself may not
# exist yet on a fresh clone, so bootstrapping it *through* the Taskfile
# would be circular. Both local devs and CI (see checks.yaml and
# ci-gate.yaml) run the exact same two commands:
#   ./scripts/setup.sh
#   source scripts/env.sh   # put .tools/bin and .tools/node/bin on PATH for this shell session
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BIN_DIR="$REPO_ROOT/.tools/bin"
NODE_DIR="$REPO_ROOT/.tools/node"

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

if [ -x "$BIN_DIR/task" ] && version_matches "$("$BIN_DIR/task" --version)" "$TASK_VERSION"; then
    echo "task: already installed ($("$BIN_DIR/task" --version))"
else
    echo "task: installing $TASK_VERSION into $BIN_DIR ..."
    FETCH "https://taskfile.dev/install.sh" | sh -s -- -b "$BIN_DIR" "$TASK_VERSION"
    echo "task: installed ($("$BIN_DIR/task" --version))"
fi

OS="$(detect_os)"
ARCH_GNU="$(detect_arch_gnu)"
ARCH_SC="$(detect_arch_shellcheck)"

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
    "$NODE_DIR/bin/npm" install --global --prefix "$REPO_ROOT/.tools" "@fission-ai/openspec@${OPENSPEC_VERSION}"
    echo "openspec: installed ($("$BIN_DIR/openspec" --version))"
fi

echo
echo "Setup complete. Run 'source scripts/env.sh' to put .tools/bin and .tools/node/bin on PATH, then 'task shell:lint'."
