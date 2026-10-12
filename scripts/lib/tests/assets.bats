#!/usr/bin/env bats
# Unit tests for scripts/lib/assets.sh: asset_url's per-tool, per-platform
# URL shapes, plus the invariant that scripts/lib/checksums.txt pins
# exactly the URLs asset_url can produce at the current versions -
# so a version bump without a refreshed checksums.txt fails here, not
# only on the next fresh `task setup`.

load '../versions.sh'
load '../assets.sh'

@test "asset_url: task uses its own os/arch naming and keeps the leading v" {
    run asset_url task linux arm64
    [ "$status" -eq 0 ]
    [ "$output" = "https://github.com/go-task/task/releases/download/${TASK_VERSION}/task_linux_arm64.tar.gz" ]
}

@test "asset_url: shellcheck uses x86_64/aarch64 arch naming" {
    run asset_url shellcheck darwin amd64
    [ "$status" -eq 0 ]
    [ "$output" = "https://github.com/koalaman/shellcheck/releases/download/v${SHELLCHECK_VERSION}/shellcheck-v${SHELLCHECK_VERSION}.darwin.x86_64.tar.gz" ]
}

@test "asset_url: node uses x64 arch naming" {
    run asset_url node linux amd64
    [ "$status" -eq 0 ]
    [ "$output" = "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.gz" ]
}

@test "asset_url: uv uses a Rust target triple" {
    run asset_url uv linux arm64
    [ "$status" -eq 0 ]
    [ "$output" = "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-aarch64-unknown-linux-gnu.tar.gz" ]
}

@test "asset_url: rejects an unknown tool, OS, or architecture" {
    run asset_url nope linux amd64
    [ "$status" -ne 0 ]
    run asset_url task plan9 amd64
    [ "$status" -ne 0 ]
    run asset_url task linux riscv
    [ "$status" -ne 0 ]
}

@test "checksums.txt pins exactly the URLs asset_url produces for every tool and platform" {
    local expected actual tool platform
    expected="$(
        for tool in "${ASSET_TOOLS[@]}"; do
            for platform in "${SUPPORTED_PLATFORMS[@]}"; do
                asset_url "$tool" "${platform%-*}" "${platform#*-}"
            done
        done | sort -u
    )"
    actual="$(awk '{print $2}' "$BATS_TEST_DIRNAME/../checksums.txt" | sort -u)"
    [ "$expected" = "$actual" ]
}

@test "checksums.txt lines are well-formed sha256 digests" {
    run grep -vcE '^[0-9a-f]{64}  https://[^ ]+$' "$BATS_TEST_DIRNAME/../checksums.txt"
    [ "$output" = "0" ]
}
