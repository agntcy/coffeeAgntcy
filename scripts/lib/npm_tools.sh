#!/usr/bin/env bash
# Generates the package.json for the npm-installed tools (openspec,
# renovate) from the pins in scripts/lib/versions.sh, so versions.sh stays
# the single place every tool version lives. Only the lockfile next to this
# file's siblings (scripts/lib/npm-tools/package-lock.json) is committed;
# `npm ci` rejects it if it no longer matches the package.json generated
# here, so a versions.sh bump without a refreshed lockfile fails loudly
# (refresh with `task tools:npm-lock`).
#
# Requires scripts/lib/versions.sh to be sourced already. Shared by
# scripts/setup.sh and scripts/tools/update_npm_lock.bash so both always
# produce the byte-identical file.
#
# shellcheck disable=SC2329  # called by whatever sources this file, not here

# write_npm_tools_package_json <dir>: writes <dir>/package.json.
write_npm_tools_package_json() {
    cat >"$1/package.json" <<JSON
{
  "name": "coffeeagntcy-repo-tools",
  "version": "0.0.0",
  "private": true,
  "dependencies": {
    "@fission-ai/openspec": "${OPENSPEC_VERSION}",
    "renovate": "${RENOVATE_VERSION}"
  }
}
JSON
}
