#!/usr/bin/env bash
# Download URLs for every tool archive scripts/setup.sh fetches directly
# (npm-installed tools are not covered here). Shared by scripts/setup.sh
# (current platform) and scripts/tools/update_checksums.bash (every
# supported platform) so both always agree on exactly which URLs exist -
# and therefore which URLs scripts/lib/checksums.txt must hold a SHA-256
# for.
#
# Requires scripts/lib/versions.sh to be sourced already.
#
# shellcheck disable=SC2329,SC2034  # functions and arrays are used by whatever sources this file, not here

# Platforms the toolchain supports: "<os>-<arch>", os in darwin|linux and
# arch in amd64|arm64 (the naming platform.sh's detect_os/detect_arch_gnu
# print).
SUPPORTED_PLATFORMS=(darwin-amd64 darwin-arm64 linux-amd64 linux-arm64)

# Tools with a directly downloaded archive, alphabetical.
ASSET_TOOLS=(actionlint bats node shellcheck shfmt task uv)

# asset_url <tool> <os> <arch>
asset_url() {
    local tool="$1" os="$2" arch="$3"
    local arch_sc arch_node triple uv_os
    case "$arch" in
        amd64)
            arch_sc=x86_64
            arch_node=x64
            ;;
        arm64)
            arch_sc=aarch64
            arch_node=arm64
            ;;
        *)
            echo "error: unsupported architecture '$arch'" >&2
            return 1
            ;;
    esac
    case "$os" in
        darwin) uv_os=apple-darwin ;;
        linux) uv_os=unknown-linux-gnu ;;
        *)
            echo "error: unsupported OS '$os'" >&2
            return 1
            ;;
    esac
    triple="${arch_sc}-${uv_os}"

    case "$tool" in
        actionlint) echo "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_${os}_${arch}.tar.gz" ;;
        bats) echo "https://github.com/bats-core/bats-core/archive/refs/tags/v${BATS_VERSION}.tar.gz" ;;
        node) echo "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-${os}-${arch_node}.tar.gz" ;;
        shellcheck) echo "https://github.com/koalaman/shellcheck/releases/download/v${SHELLCHECK_VERSION}/shellcheck-v${SHELLCHECK_VERSION}.${os}.${arch_sc}.tar.gz" ;;
        shfmt) echo "https://github.com/mvdan/sh/releases/download/v${SHFMT_VERSION}/shfmt_v${SHFMT_VERSION}_${os}_${arch}" ;;
        task) echo "https://github.com/go-task/task/releases/download/${TASK_VERSION}/task_${os}_${arch}.tar.gz" ;;
        uv) echo "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-${triple}.tar.gz" ;;
        *)
            echo "error: unknown tool '$tool'" >&2
            return 1
            ;;
    esac
}
