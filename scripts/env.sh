#!/usr/bin/env bash
# Puts this repo's local toolchain (.tools/bin, .tools/node/bin,
# .tools/bats/bin) on PATH for the current shell. .tools/node/bin and
# .tools/bats/bin are separate from .tools/bin because node's own
# npm/npx are symlinks resolved relative to a sibling
# lib/node_modules/npm/, and bats-core's own install.sh always creates a
# bin/+libexec/+lib/ tree together - so both ship as a whole directory
# tree rather than a single relocatable binary like everything else in
# .tools/bin.
# Usage: source scripts/env.sh   (run from anywhere inside the repo)
_coffeeagntcy_repo_root() {
    git rev-parse --show-toplevel 2>/dev/null || pwd
}

_repo_root="$(_coffeeagntcy_repo_root)"
export PATH="$_repo_root/.tools/bin:$_repo_root/.tools/node/bin:$_repo_root/.tools/bats/bin:$PATH"
# Export only NODE_VERSION and UV_VERSION. The other pins stay inside
# this subshell so an image build can read those two pins without taking
# the rest of the toolchain versions into the environment.
NODE_VERSION="$(
    # shellcheck source=scripts/lib/versions.sh
    . "$_repo_root/scripts/lib/versions.sh"
    printf '%s' "$NODE_VERSION"
)"
export NODE_VERSION
UV_VERSION="$(
    # shellcheck source=scripts/lib/versions.sh
    . "$_repo_root/scripts/lib/versions.sh"
    printf '%s' "$UV_VERSION"
)"
export UV_VERSION
unset -f _coffeeagntcy_repo_root
unset _repo_root
