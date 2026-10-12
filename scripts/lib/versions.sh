#!/usr/bin/env bash
# Pinned tool versions, sourced by scripts/setup.sh.
# Bump here only.
# The pins below are alphabetical by variable name; scripts/setup.sh installs in
# dependency order instead (node before the npm-installed openspec/renovate).
# openspec/renovate also get a committed lockfile (scripts/lib/npm-tools/);
# after bumping either, run `task tools:npm-lock` (and `task tools:checksums`
# after bumping any of the others).
# shellcheck disable=SC2034  # consumed by whatever sources this file, not here

# renovate: datasource=github-releases depName=rhysd/actionlint extractVersion=^v(?<version>.*)$
ACTIONLINT_VERSION="1.7.12"
# renovate: datasource=github-releases depName=bats-core/bats-core extractVersion=^v(?<version>.*)$
BATS_VERSION="1.13.0" # bats-core git tag, installed from its own source tarball - not the npm "bats" package version
# renovate: datasource=node-version depName=node
NODE_VERSION="24.21.0"
# renovate: datasource=npm depName=@fission-ai/openspec
OPENSPEC_VERSION="1.13.2"
# renovate: datasource=npm depName=renovate
RENOVATE_VERSION="44.127.1"
# renovate: datasource=github-releases depName=koalaman/shellcheck extractVersion=^v(?<version>.*)$
SHELLCHECK_VERSION="0.11.0"
# renovate: datasource=github-releases depName=mvdan/sh extractVersion=^v(?<version>.*)$
SHFMT_VERSION="3.14.1"
# renovate: datasource=github-releases depName=go-task/task
TASK_VERSION="v3.53.1"
# renovate: datasource=github-releases depName=astral-sh/uv
UV_VERSION="0.12.23"
