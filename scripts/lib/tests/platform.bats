#!/usr/bin/env bats
# Unit tests for scripts/lib/platform.sh's OS/arch detection functions,
# mocking `uname` so every branch (including the unsupported-input error
# path) is exercised deterministically, regardless of what machine these
# tests actually run on.

load '../testing.sh'
load '../platform.sh'

setup() {
    mock_setup
}

teardown() {
    mock_teardown
}

@test "detect_os: Darwin maps to darwin" {
    mock_command uname 'echo Darwin'
    run detect_os
    [ "$status" -eq 0 ]
    [ "$output" = "darwin" ]
}

@test "detect_os: Linux maps to linux" {
    mock_command uname 'echo Linux'
    run detect_os
    [ "$status" -eq 0 ]
    [ "$output" = "linux" ]
}

@test "detect_os: an unsupported OS fails with an error" {
    mock_command uname 'echo Plan9'
    run detect_os
    [ "$status" -ne 0 ]
    [[ "$output" == *"unsupported OS 'Plan9'"* ]]
}

@test "detect_arch_gnu: x86_64/amd64 map to amd64" {
    mock_command uname 'echo x86_64'
    run detect_arch_gnu
    [ "$status" -eq 0 ]
    [ "$output" = "amd64" ]

    mock_command uname 'echo amd64'
    run detect_arch_gnu
    [ "$status" -eq 0 ]
    [ "$output" = "amd64" ]
}

@test "detect_arch_gnu: arm64/aarch64 map to arm64" {
    mock_command uname 'echo arm64'
    run detect_arch_gnu
    [ "$status" -eq 0 ]
    [ "$output" = "arm64" ]

    mock_command uname 'echo aarch64'
    run detect_arch_gnu
    [ "$status" -eq 0 ]
    [ "$output" = "arm64" ]
}

@test "detect_arch_gnu: an unsupported arch fails with an error" {
    mock_command uname 'echo riscv64'
    run detect_arch_gnu
    [ "$status" -ne 0 ]
    [[ "$output" == *"unsupported architecture 'riscv64'"* ]]
}

@test "detect_arch_shellcheck: x86_64/amd64 map to x86_64" {
    mock_command uname 'echo amd64'
    run detect_arch_shellcheck
    [ "$status" -eq 0 ]
    [ "$output" = "x86_64" ]
}

@test "detect_arch_shellcheck: arm64/aarch64 map to aarch64" {
    mock_command uname 'echo arm64'
    run detect_arch_shellcheck
    [ "$status" -eq 0 ]
    [ "$output" = "aarch64" ]
}

@test "detect_arch_node: x86_64/amd64 map to x64" {
    mock_command uname 'echo x86_64'
    run detect_arch_node
    [ "$status" -eq 0 ]
    [ "$output" = "x64" ]
}

@test "detect_arch_node: arm64/aarch64 map to arm64" {
    mock_command uname 'echo aarch64'
    run detect_arch_node
    [ "$status" -eq 0 ]
    [ "$output" = "arm64" ]
}

@test "detect_triple_uv: maps each supported OS/arch pair to uv's target triple" {
    mock_command uname 'case "$1" in -s) echo Darwin ;; -m) echo arm64 ;; esac'
    run detect_triple_uv
    [ "$status" -eq 0 ]
    [ "$output" = "aarch64-apple-darwin" ]

    mock_command uname 'case "$1" in -s) echo Linux ;; -m) echo x86_64 ;; esac'
    run detect_triple_uv
    [ "$status" -eq 0 ]
    [ "$output" = "x86_64-unknown-linux-gnu" ]
}

@test "detect_triple_uv: an unsupported arch or OS fails with an error" {
    mock_command uname 'case "$1" in -s) echo Linux ;; -m) echo riscv64 ;; esac'
    run detect_triple_uv
    [ "$status" -ne 0 ]
    [[ "$output" == *"unsupported architecture 'riscv64'"* ]]

    mock_command uname 'case "$1" in -s) echo Plan9 ;; -m) echo x86_64 ;; esac'
    run detect_triple_uv
    [ "$status" -ne 0 ]
    [[ "$output" == *"unsupported OS 'Plan9'"* ]]
}
