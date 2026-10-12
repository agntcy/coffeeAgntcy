#!/usr/bin/env bash
# Ensures a fetcher (curl, falling back to wget) is available, attempting to
# install curl via a detected OS package manager if neither is present.
# On success, defines FETCH() so `FETCH <url>` streams the URL to stdout.
#
# curl itself can't be used to fetch curl, and installing wget instead just
# moves the problem, so this only ever tries to install curl - via whatever
# package manager (common to macOS and Linux) is already on the machine. If
# none is found, or more than one is and the session isn't interactive, it
# prints manual instructions and fails rather than guessing.
#
# shellcheck disable=SC2329  # FETCH() is called by whatever sources this file, not here

_install_curl_with() {
    local manager="$1"
    local sudo_prefix=()
    if [ "$(id -u)" != "0" ] && command -v sudo >/dev/null 2>&1; then
        sudo_prefix=(sudo)
    fi

    case "$manager" in
        brew)
            brew install curl
            ;;
        apt-get)
            "${sudo_prefix[@]}" apt-get update -y
            "${sudo_prefix[@]}" apt-get install -y curl
            ;;
        dnf)
            "${sudo_prefix[@]}" dnf install -y curl
            ;;
        yum)
            "${sudo_prefix[@]}" yum install -y curl
            ;;
        apk)
            "${sudo_prefix[@]}" apk add --no-cache curl
            ;;
        pacman)
            "${sudo_prefix[@]}" pacman -Sy --noconfirm curl
            ;;
        zypper)
            "${sudo_prefix[@]}" zypper install -y curl
            ;;
        *)
            return 1
            ;;
    esac
}

_print_manual_curl_instructions() {
    echo >&2
    echo "Could not find or install curl/wget automatically." >&2
    echo "Install one of them yourself, then re-run ./scripts/setup.sh:" >&2
    echo "  macOS:         brew install curl" >&2
    echo "  Debian/Ubuntu: sudo apt-get install -y curl" >&2
    echo "  Fedora:        sudo dnf install -y curl" >&2
    echo "  RHEL/CentOS:   sudo yum install -y curl" >&2
    echo "  Alpine:        sudo apk add curl" >&2
    echo "  Arch:          sudo pacman -S curl" >&2
    echo "  openSUSE:      sudo zypper install curl" >&2
}

ensure_fetcher() {
    if command -v curl >/dev/null 2>&1; then
        FETCH() { curl -fsSL "$1"; }
        return 0
    fi
    if command -v wget >/dev/null 2>&1; then
        FETCH() { wget -qO- "$1"; }
        return 0
    fi

    echo "curl/wget not found - looking for a package manager to install curl with ..." >&2

    local candidates=()
    local manager
    for manager in brew apt-get dnf yum apk pacman zypper; do
        if command -v "$manager" >/dev/null 2>&1; then
            candidates+=("$manager")
        fi
    done

    local chosen=""
    if [ "${#candidates[@]}" -eq 1 ]; then
        chosen="${candidates[0]}"
    elif [ "${#candidates[@]}" -gt 1 ] && [ -t 0 ] && [ -t 1 ]; then
        echo "Multiple package managers found:" >&2
        local i=1
        local c
        for c in "${candidates[@]}"; do
            echo "  $i) $c" >&2
            i=$((i + 1))
        done
        local pick
        printf "Choose one to install curl with [1-%d]: " "${#candidates[@]}" >&2
        read -r pick
        case "$pick" in
            '' | *[!0-9]*) chosen="" ;;
            *)
                if [ "$pick" -ge 1 ] && [ "$pick" -le "${#candidates[@]}" ]; then
                    chosen="${candidates[$((pick - 1))]}"
                fi
                ;;
        esac
    fi
    # Non-interactive with more than one candidate falls through with
    # $chosen unset: fail closed with manual instructions below, rather than
    # silently picking one and running a possibly-sudo install nobody agreed
    # to (and GitHub-hosted runners already ship curl, so CI never reaches
    # this branch anyway).

    if [ -n "$chosen" ]; then
        echo "Installing curl via: $chosen" >&2
        if _install_curl_with "$chosen" >&2 && command -v curl >/dev/null 2>&1; then
            FETCH() { curl -fsSL "$1"; }
            return 0
        fi
        echo "warning: installing curl via '$chosen' did not succeed." >&2
    fi

    _print_manual_curl_instructions
    return 1
}

# sha256_of <file>: prints the file's SHA-256 hex digest, using whichever of
# sha256sum (Linux) or shasum (macOS) exists.
sha256_of() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        echo "error: neither sha256sum nor shasum found" >&2
        return 1
    fi
}

# FETCH_VERIFIED <url>: like FETCH, but streams the URL to stdout only if
# its SHA-256 matches the one pinned for that exact URL in
# $CHECKSUMS_FILE (default: checksums.txt next to this file; lines are
# "<sha256>  <url>"). Fails closed: a URL with no pinned checksum, or a
# mismatch, prints an error to stderr and emits nothing. A version bump
# changes the URL, so it needs a refreshed checksums.txt
# (task tools:checksums) before setup will install it.
FETCH_VERIFIED() {
    local url="$1"
    local file="${CHECKSUMS_FILE:-$(dirname "${BASH_SOURCE[0]}")/checksums.txt}"
    local expected actual tmp
    if [ -z "$url" ]; then
        echo "error: FETCH_VERIFIED called without a URL" >&2
        return 1
    fi
    expected="$(awk -v u="$url" '$2 == u {print $1}' "$file" 2>/dev/null | head -n 1)"
    if [ -z "$expected" ]; then
        echo "error: no pinned checksum for $url in $file (run: task tools:checksums)" >&2
        return 1
    fi
    tmp="$(mktemp)"
    if ! FETCH "$url" >"$tmp"; then
        rm -f "$tmp"
        return 1
    fi
    actual="$(sha256_of "$tmp")" || {
        rm -f "$tmp"
        return 1
    }
    if [ "$actual" != "$expected" ]; then
        echo "error: checksum mismatch for $url" >&2
        echo "  expected: $expected" >&2
        echo "  actual:   $actual" >&2
        rm -f "$tmp"
        return 1
    fi
    cat "$tmp"
    rm -f "$tmp"
}
