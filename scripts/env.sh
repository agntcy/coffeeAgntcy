#!/usr/bin/env bash
# Puts this repo's local toolchain (.tools/bin, .tools/node/bin) on PATH for
# the current shell. .tools/node/bin is separate from .tools/bin because
# node's own npm/npx are symlinks resolved relative to a sibling
# lib/node_modules/npm/, so node ships as a whole directory tree rather than
# a single relocatable binary like everything else in .tools/bin.
# Usage: source scripts/env.sh   (run from anywhere inside the repo)
_coffeeagntcy_repo_root() {
    git rev-parse --show-toplevel 2>/dev/null || pwd
}

_repo_root="$(_coffeeagntcy_repo_root)"
export PATH="$_repo_root/.tools/bin:$_repo_root/.tools/node/bin:$PATH"
unset -f _coffeeagntcy_repo_root
unset _repo_root
