#!/usr/bin/env bash
# Pinned tool versions, sourced by scripts/setup.sh.
# Bump here only.
# shellcheck disable=SC2034  # consumed by whatever sources this file, not here

# renovate: datasource=github-releases depName=go-task/task
TASK_VERSION="v3.53.1"
# renovate: datasource=github-releases depName=rhysd/actionlint extractVersion=^v(?<version>.*)$
ACTIONLINT_VERSION="1.7.12"
# renovate: datasource=github-releases depName=koalaman/shellcheck extractVersion=^v(?<version>.*)$
SHELLCHECK_VERSION="0.11.0"
# renovate: datasource=github-releases depName=mvdan/sh extractVersion=^v(?<version>.*)$
SHFMT_VERSION="3.14.1"
# renovate: datasource=node-version depName=node
NODE_VERSION="24.21.0"
# renovate: datasource=npm depName=@fission-ai/openspec
OPENSPEC_VERSION="1.13.2"
# renovate: datasource=npm depName=renovate
RENOVATE_VERSION="44.127.1"
