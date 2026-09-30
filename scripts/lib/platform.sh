#!/usr/bin/env bash
# OS/arch detection shared by scripts/setup.sh's static-binary installs
# (actionlint, shellcheck, shfmt, node -- task ships its own installer with
# its own detection).

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

# x86_64/aarch64 naming, as used by shellcheck release assets.
detect_arch_shellcheck() {
    case "$(uname -m)" in
        x86_64 | amd64) echo x86_64 ;;
        arm64 | aarch64) echo aarch64 ;;
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
