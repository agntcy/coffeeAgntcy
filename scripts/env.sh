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
unset -f _coffeeagntcy_repo_root
unset _repo_root
