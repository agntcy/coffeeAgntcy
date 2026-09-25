#!/usr/bin/env bash
# Puts this repo's local toolchain (.tools/bin) on PATH for the current
# shell. Usage: source scripts/env.sh   (run from anywhere inside the repo)
_coffeeagntcy_repo_root() {
    git rev-parse --show-toplevel 2>/dev/null || pwd
}

_repo_root="$(_coffeeagntcy_repo_root)"
export PATH="$_repo_root/.tools/bin:$PATH"
unset -f _coffeeagntcy_repo_root
unset _repo_root
