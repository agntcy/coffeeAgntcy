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
    elif [ "${#candidates[@]}" -gt 1 ]; then
        # Non-interactive (e.g. CI) with more than one candidate: just take the
        # first rather than blocking on a prompt nobody can answer.
        chosen="${candidates[0]}"
    fi

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
