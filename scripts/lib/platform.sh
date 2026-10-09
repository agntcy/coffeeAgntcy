#!/usr/bin/env bash
# OS/arch detection used by scripts/setup.sh to pick the current machine's
# archive (scripts/lib/assets.sh holds the per-tool URL and naming rules).

detect_os() {
    case "$(uname -s)" in
        Darwin) echo darwin ;;
        Linux) echo linux ;;
        *)
            echo "error: unsupported OS '$(uname -s)'" >&2
            return 1
            ;;
    esac
}

# amd64/arm64 naming, as used by actionlint and shfmt release assets.
detect_arch_gnu() {
    case "$(uname -m)" in
        x86_64 | amd64) echo amd64 ;;
        arm64 | aarch64) echo arm64 ;;
        *)
            echo "error: unsupported architecture '$(uname -m)'" >&2
            return 1
            ;;
    esac
}

# x64/arm64 naming, as used by Node.js release tarballs.
detect_arch_node() {
    case "$(uname -m)" in
        x86_64 | amd64) echo x64 ;;
        arm64 | aarch64) echo arm64 ;;
        *)
            echo "error: unsupported architecture '$(uname -m)'" >&2
            return 1
            ;;
    esac
}

# Rust target triple, as used by uv release assets
# (uv-<triple>.tar.gz, e.g. aarch64-apple-darwin, x86_64-unknown-linux-gnu).
detect_triple_uv() {
    local arch os
    case "$(uname -m)" in
        x86_64 | amd64) arch=x86_64 ;;
        arm64 | aarch64) arch=aarch64 ;;
        *)
            echo "error: unsupported architecture '$(uname -m)'" >&2
            return 1
            ;;
    esac
    case "$(uname -s)" in
        Darwin) os=apple-darwin ;;
        Linux) os=unknown-linux-gnu ;;
        *)
            echo "error: unsupported OS '$(uname -s)'" >&2
            return 1
            ;;
    esac
    echo "${arch}-${os}"
}
