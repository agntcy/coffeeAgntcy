#!/usr/bin/env bats
# Unit tests for scripts/lib/fetch.sh's ensure_fetcher/_install_curl_with/
# _print_manual_curl_instructions, mocking curl/wget/package-manager
# binaries so every branch (curl present, wget fallback, single/multiple
# package-manager candidates, none found) is exercised deterministically,
# regardless of what's actually installed on the machine running these
# tests.
#
# The tricky part: real curl/wget/sudo/apt-get/id are on PATH wherever
# these tests run, so "curl is absent" (or "sudo is absent") can't be
# simulated by mock_command alone (its stubs only add to PATH, they
# can't hide a real binary elsewhere on PATH). For branches that need one
# of those genuinely absent, tests use mock_isolate_path (see
# scripts/lib/testing.sh) rather than guessing a system directory that
# happens not to contain it - a guess like that doesn't port across OSes
# (Debian/Ubuntu's merged-usr layout makes bare /bin reach everything
# /usr/bin has, including curl/wget/sudo/apt-get/id, unlike macOS's
# separate, minimal /bin).

load '../testing.sh'
load '../fetch.sh'

setup() {
    mock_setup
}

teardown() {
    mock_teardown
}

@test "ensure_fetcher: curl present defines FETCH via curl -fsSL" {
    mock_command curl 'echo "curl called with: $*"'

    local status=0
    ensure_fetcher || status=$?
    [ "$status" -eq 0 ]

    run FETCH "http://example.test"
    [ "$status" -eq 0 ]
    [ "$output" = "curl called with: -fsSL http://example.test" ]
}

@test "ensure_fetcher: curl absent, wget present defines FETCH via wget -qO-" {
    mock_isolate_path bash chmod
    mock_command wget 'echo "wget called with: $*"'

    local status=0
    ensure_fetcher || status=$?
    [ "$status" -eq 0 ]

    run FETCH "http://example.test"
    [ "$status" -eq 0 ]
    [ "$output" = "wget called with: -qO- http://example.test" ]
}

@test "ensure_fetcher: neither curl nor wget, one package manager found installs curl with it" {
    mock_isolate_path bash chmod
    mock_command id 'echo 1000'
    mock_command apt-get "printf '#!/usr/bin/env bash\necho apt-get-curl \"\$*\"\n' > '$MOCK_BIN_DIR/curl'
chmod +x '$MOCK_BIN_DIR/curl'"

    local stderr_file="$BATS_TEST_TMPDIR/stderr.txt"
    local status=0
    ensure_fetcher 2>"$stderr_file" || status=$?
    [ "$status" -eq 0 ]
    local stderr_text
    stderr_text="$(<"$stderr_file")"
    [[ "$stderr_text" == *"Installing curl via: apt-get"* ]]

    run FETCH "http://example.test"
    [ "$status" -eq 0 ]
    [ "$output" = "apt-get-curl -fsSL http://example.test" ]
}

@test "ensure_fetcher: multiple package managers found, non-interactive picks the first without prompting" {
    mock_isolate_path bash chmod
    mock_command id 'echo 1000'
    mock_command apt-get "printf '#!/usr/bin/env bash\necho apt-get-curl \"\$*\"\n' > '$MOCK_BIN_DIR/curl'
chmod +x '$MOCK_BIN_DIR/curl'"
    mock_command dnf "printf '' > '$BATS_TEST_TMPDIR/dnf-was-called'"

    local stderr_file="$BATS_TEST_TMPDIR/stderr.txt"
    local status=0
    ensure_fetcher 2>"$stderr_file" || status=$?
    [ "$status" -eq 0 ]
    local stderr_text
    stderr_text="$(<"$stderr_file")"
    [[ "$stderr_text" == *"Installing curl via: apt-get"* ]]
    [[ "$stderr_text" != *"Multiple package managers found"* ]]
    [ ! -e "$BATS_TEST_TMPDIR/dnf-was-called" ]

    run FETCH "http://example.test"
    [ "$status" -eq 0 ]
    [ "$output" = "apt-get-curl -fsSL http://example.test" ]
}

@test "ensure_fetcher: no package manager found prints manual instructions and fails" {
    mock_isolate_path bash chmod

    run ensure_fetcher
    [ "$status" -eq 1 ]
    [[ "$output" == *"curl/wget not found"* ]]
    [[ "$output" == *"Could not find or install curl/wget automatically."* ]]
    [[ "$output" == *"brew install curl"* ]]
}

@test "ensure_fetcher: install succeeding but curl still missing falls back to manual instructions" {
    mock_isolate_path bash chmod
    mock_command id 'echo 1000'
    mock_command apt-get 'exit 0'

    run ensure_fetcher
    [ "$status" -eq 1 ]
    [[ "$output" == *"warning: installing curl via 'apt-get' did not succeed."* ]]
    [[ "$output" == *"Could not find or install curl/wget automatically."* ]]
}

@test "_install_curl_with: brew dispatches to brew install curl" {
    mock_command brew 'echo "brew called with: $*"'

    run _install_curl_with brew
    [ "$status" -eq 0 ]
    [ "$output" = "brew called with: install curl" ]
}

@test "_install_curl_with: apt-get dispatches to apt-get update then install" {
    mock_isolate_path bash chmod
    mock_command id 'echo 1000'
    mock_command apt-get 'echo "apt-get called with: $*"'

    run _install_curl_with apt-get
    [ "$status" -eq 0 ]
    [[ "$output" == *"apt-get called with: update -y"* ]]
    [[ "$output" == *"apt-get called with: install -y curl"* ]]
}

@test "_install_curl_with: prefixes sudo when not root and sudo is available" {
    mock_command id 'echo 1000'
    mock_command sudo 'echo "sudo called with: $*"; "$@"'
    mock_command apt-get 'echo "apt-get called with: $*"'

    run _install_curl_with apt-get
    [ "$status" -eq 0 ]
    [[ "$output" == *"sudo called with: apt-get update -y"* ]]
    [[ "$output" == *"sudo called with: apt-get install -y curl"* ]]
}

@test "_install_curl_with: skips sudo when already root" {
    mock_command id 'echo 0'
    mock_command apt-get 'echo "apt-get called with: $*"'

    run _install_curl_with apt-get
    [ "$status" -eq 0 ]
    [[ "$output" != *"sudo"* ]]
    [[ "$output" == *"apt-get called with: update -y"* ]]
}

@test "_install_curl_with: unsupported manager returns 1" {
    run _install_curl_with some-unknown-manager
    [ "$status" -eq 1 ]
}

@test "_print_manual_curl_instructions: prints instructions for every supported platform" {
    run _print_manual_curl_instructions
    [ "$status" -eq 0 ]
    [[ "$output" == *"brew install curl"* ]]
    [[ "$output" == *"apt-get install -y curl"* ]]
    [[ "$output" == *"dnf install -y curl"* ]]
    [[ "$output" == *"yum install -y curl"* ]]
    [[ "$output" == *"apk add curl"* ]]
    [[ "$output" == *"pacman -S curl"* ]]
    [[ "$output" == *"zypper install curl"* ]]
}
