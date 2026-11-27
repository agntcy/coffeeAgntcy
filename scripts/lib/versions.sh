#!/usr/bin/env bash
# Pinned tool versions, sourced by scripts/setup.sh.
# Bump here only.
# The pins below are alphabetical by variable name; scripts/setup.sh installs in
# dependency order instead (node before the npm-installed openspec/renovate).
# openspec/renovate also get a committed lockfile (scripts/lib/npm-tools/);
# after bumping either, run `task tools:npm-lock`. sigstore also gets a
# committed hash-pinned requirements file (scripts/lib/sigstore/); after
# bumping SIGSTORE_VERSION, run `task tools:sigstore-lock`, then
# `task tools:checksums`. Run `task tools:checksums` after bumping any
# other pin too.
# shellcheck disable=SC2034  # consumed by whatever sources this file, not here

# renovate: datasource=github-releases depName=rhysd/actionlint extractVersion=^v(?<version>.*)$
ACTIONLINT_VERSION="1.7.12"
# renovate: datasource=github-releases depName=bats-core/bats-core extractVersion=^v(?<version>.*)$
BATS_VERSION="1.14.0" # bats-core git tag, installed from its own source tarball - not the npm "bats" package version
# renovate: datasource=github-releases depName=agntcy/dir-mcp versioning=regex:^(?<major>\d+)\.(?<minor>\d+)\.(?<patch>\d+)(?:-mcp\.(?<build>\d+))?$ extractVersion=^v(?<version>.*)$
DIR_MCP_VERSION="1.3.8-mcp.1"
# renovate: datasource=github-releases depName=helm/helm
HELM_VERSION="v4.3.0"
# renovate: datasource=node-version depName=node
NODE_VERSION="26.13.1"
# renovate: datasource=npm depName=@fission-ai/openspec
OPENSPEC_VERSION="1.13.2"
# renovate: datasource=npm depName=renovate
RENOVATE_VERSION="44.219.0"
# renovate: datasource=github-releases depName=koalaman/shellcheck extractVersion=^v(?<version>.*)$
SHELLCHECK_VERSION="0.11.0"
# renovate: datasource=github-releases depName=mvdan/sh extractVersion=^v(?<version>.*)$
SHFMT_VERSION="3.14.1"
# renovate: datasource=pypi depName=sigstore
SIGSTORE_VERSION="4.5.1"
# renovate: datasource=github-releases depName=go-task/task
TASK_VERSION="v3.53.1"
# renovate: datasource=github-releases depName=astral-sh/uv
UV_VERSION="0.12.23"
