#!/usr/bin/env bats
# Mocked end-to-end test for update_checksums.bash: curl is mocked to
# serve the URL itself as content, so each expected hash can be computed
# independently here, and CHECKSUMS_FILE points at a fixture instead of
# the real scripts/lib/checksums.txt. uv is mocked too (the dir-mcp
# sigstore verification runs through a hash-pinned venv): the stub logs its
# argv to UV_LOG; `uv venv <dir>` creates <dir>/bin/sigstore, a stub that
# logs its argv and the content of the --bundle file to VERIFY_LOG and exits
# non-zero when the asset it was asked to verify contains VERIFY_FAIL_ON;
# `uv pip install` exits non-zero when UV_INSTALL_FAIL is set (simulating a
# hash mismatch). SIGSTORE_REQUIREMENTS_FILE points at a fixture that pins
# the same sigstore version as versions.sh.

load '../../lib/testing.sh'

SCRIPT="$BATS_TEST_DIRNAME/../update_checksums.bash"

setup() {
    mock_setup
    mock_command curl 'echo "${*: -1}" >>"$CURL_LOG"; printf "%s" "${*: -1}"'
    mock_command uv 'echo "$*" >>"$UV_LOG"
[ "$1" = "--no-config" ] && shift
case "$1 $2" in
"venv "*)
    venv="${*: -1}"
    mkdir -p "$venv/bin"
    cat >"$venv/bin/sigstore" <<'"'"'STUB'"'"'
echo "$*" >>"$VERIFY_LOG"
asset="${*: -1}"
while [ $# -gt 0 ]; do
    [ "$1" = "--bundle" ] && echo "bundle-content: $(cat "$2")" >>"$VERIFY_LOG"
    shift
done
if [ -n "${VERIFY_FAIL_ON:-}" ] && grep -qF "$VERIFY_FAIL_ON" "$asset" 2>/dev/null; then
    exit 1
fi
STUB
    chmod +x "$venv/bin/sigstore"
    ;;
"pip install")
    if [ -n "${UV_INSTALL_FAIL:-}" ]; then
        echo "error: hash mismatch" >&2
        exit 1
    fi
    ;;
esac'
    # The script prefers UV_BIN over .tools/bin/uv and PATH: point it at the mock.
    export UV_BIN="$MOCK_BIN_DIR/uv"
    export CURL_LOG="$BATS_TEST_TMPDIR/curl.log"
    export UV_LOG="$BATS_TEST_TMPDIR/uv.log"
    export VERIFY_LOG="$BATS_TEST_TMPDIR/verify.log"
    : >"$CURL_LOG"
    : >"$UV_LOG"
    : >"$VERIFY_LOG"
    export CHECKSUMS_FILE="$BATS_TEST_TMPDIR/checksums.txt"
    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/versions.sh"
    export SIGSTORE_REQUIREMENTS_FILE="$BATS_TEST_TMPDIR/requirements.txt"
    printf 'sigstore==%s \\\n    --hash=sha256:00\n' "$SIGSTORE_VERSION" >"$SIGSTORE_REQUIREMENTS_FILE"
}

teardown() {
    mock_teardown
}

@test "writes one sorted '<sha256>  <url>' line per distinct asset URL" {
    run "$SCRIPT"
    [ "$status" -eq 0 ]

    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/versions.sh"
    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/assets.sh"
    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/fetch.sh"

    run grep -vcE '^[0-9a-f]{64}  https://[^ ]+$' "$CHECKSUMS_FILE"
    [ "$output" = "0" ]

    [ "$(awk '{print $2}' "$CHECKSUMS_FILE")" = "$(awk '{print $2}' "$CHECKSUMS_FILE" | LC_ALL=C sort)" ]
    [ "$(awk '{print $2}' "$CHECKSUMS_FILE" | sort -u | wc -l)" -eq "$(wc -l <"$CHECKSUMS_FILE")" ]

    local url expected
    url="$(asset_url task linux arm64)"
    printf '%s' "$url" >"$BATS_TEST_TMPDIR/expected"
    expected="$(sha256_of "$BATS_TEST_TMPDIR/expected")"
    grep -qxF "$expected  $url" "$CHECKSUMS_FILE"
}

@test "asset_url dir-mcp returns the raw release binary URL for every supported platform" {
    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/versions.sh"
    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/assets.sh"

    local base="https://github.com/agntcy/dir-mcp/releases/download/v${DIR_MCP_VERSION}"
    [ "$(asset_url dir-mcp darwin amd64)" = "$base/mcp-server-darwin-amd64" ]
    [ "$(asset_url dir-mcp darwin arm64)" = "$base/mcp-server-darwin-arm64" ]
    [ "$(asset_url dir-mcp linux amd64)" = "$base/mcp-server-linux-amd64" ]
    [ "$(asset_url dir-mcp linux arm64)" = "$base/mcp-server-linux-arm64" ]
}

@test "writes one line per platform for dir-mcp" {
    run "$SCRIPT"
    [ "$status" -eq 0 ]

    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/versions.sh"
    run grep -c " https://github.com/agntcy/dir-mcp/releases/download/v${DIR_MCP_VERSION}/mcp-server-\(darwin\|linux\)-\(amd64\|arm64\)\$" "$CHECKSUMS_FILE"
    [ "$output" = "4" ]
}

@test "verifies every dir-mcp asset's sigstore bundle with the hash-pinned venv's sigstore before recording it" {
    run "$SCRIPT"
    [ "$status" -eq 0 ]

    # shellcheck disable=SC1091
    source "$BATS_TEST_DIRNAME/../../lib/assets.sh"

    [ "$(wc -l <"$VERIFY_LOG" | tr -d ' ')" -eq 8 ]
    [ "$(grep -c '^verify identity ' "$VERIFY_LOG")" -eq 4 ]
    [ "$(grep -c '^tool run' "$UV_LOG")" -eq 0 ]

    local identity="https://github.com/agntcy/dir-mcp/.github/workflows/release.yml@refs/tags/v${DIR_MCP_VERSION}"
    [ "$(grep -c -- "--cert-identity ${identity} --cert-oidc-issuer https://token.actions.githubusercontent.com " "$VERIFY_LOG")" -eq 4 ]
    [ "$(grep -c -- ' --bundle ' "$VERIFY_LOG")" -eq 4 ]

    local platform url
    for platform in darwin-amd64 darwin-arm64 linux-amd64 linux-arm64; do
        url="$(asset_url dir-mcp "${platform%-*}" "${platform#*-}")"
        grep -qxF "$url.sigstore.json" "$CURL_LOG"
        grep -qxF "bundle-content: $url.sigstore.json" "$VERIFY_LOG"
    done
}

@test "creates the venv once and installs the requirements file with --no-config, --require-hashes, --no-deps and --no-build" {
    run "$SCRIPT"
    [ "$status" -eq 0 ]

    [ "$(grep -c '^--no-config venv ' "$UV_LOG")" -eq 1 ]
    [ "$(grep -c '^--no-config pip install ' "$UV_LOG")" -eq 1 ]
    local install
    install="$(grep '^--no-config pip install ' "$UV_LOG")"
    [[ "$install" == *" --require-hashes "* ]]
    [[ "$install" == *" --no-deps "* ]]
    [[ "$install" == *" --no-build "* ]]
    [[ "$install" == *" -r $SIGSTORE_REQUIREMENTS_FILE" ]]
    [[ "$install" == *"--python "*"/bin/python "* ]]
    # Only venv and pip install ever reach uv.
    [ "$(wc -l <"$UV_LOG" | tr -d ' ')" -eq 2 ]
}

@test "creates the venv on Python >=3.10 and never lets uv download an interpreter" {
    run "$SCRIPT"
    [ "$status" -eq 0 ]

    local venv
    venv="$(grep '^--no-config venv ' "$UV_LOG")"
    [[ "$venv" == *" --python >=3.10 "* ]]
    [[ "$venv" == *" --no-python-downloads "* ]]
    [[ "$venv" == *"/sigstore-venv" ]]
}

@test "UV_BIN wins over a uv on PATH" {
    mock_command uv 'echo "path-uv" >>"$UV_LOG"; exit 9'
    mkdir -p "$BATS_TEST_TMPDIR/other"
    cat >"$BATS_TEST_TMPDIR/other/uv" <<'STUB'
#!/usr/bin/env bash
echo "$*" >>"$UV_LOG"
venv="${*: -1}"
if [ "$2" = "venv" ]; then
    mkdir -p "$venv/bin"
    echo "#!/usr/bin/env bash" >"$venv/bin/sigstore"
    chmod +x "$venv/bin/sigstore"
fi
STUB
    chmod +x "$BATS_TEST_TMPDIR/other/uv"
    export UV_BIN="$BATS_TEST_TMPDIR/other/uv"

    run "$SCRIPT"
    [ "$status" -eq 0 ]
    [ "$(grep -c '^path-uv$' "$UV_LOG")" -eq 0 ]
    [ "$(grep -c '^--no-config venv ' "$UV_LOG")" -eq 1 ]
}

@test "a failing dir-mcp verification aborts, names the asset and leaves the output file untouched" {
    printf 'previous content\n' >"$CHECKSUMS_FILE"
    export VERIFY_FAIL_ON="mcp-server-linux-amd64"

    run "$SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == *"error: sigstore verification failed for "*"mcp-server-linux-amd64"* ]]
    [ "$(cat "$CHECKSUMS_FILE")" = "previous content" ]
}

@test "a failing hash-enforced install writes no dir-mcp line, verifies nothing and leaves the output file untouched" {
    printf 'previous content\n' >"$CHECKSUMS_FILE"
    export UV_INSTALL_FAIL=1

    run "$SCRIPT"
    [ "$status" -ne 0 ]
    [ "$(cat "$CHECKSUMS_FILE")" = "previous content" ]
    [ ! -s "$VERIFY_LOG" ]
}

@test "a requirements file pinning another sigstore version fails naming the lock task before any verification" {
    printf 'previous content\n' >"$CHECKSUMS_FILE"
    printf 'sigstore==0.0.1 \\\n    --hash=sha256:00\n' >"$SIGSTORE_REQUIREMENTS_FILE"

    run "$SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == *"task tools:sigstore-lock"* ]]
    [ ! -s "$VERIFY_LOG" ]
    [ ! -s "$UV_LOG" ]
    [ "$(cat "$CHECKSUMS_FILE")" = "previous content" ]
}

@test "a requirements file pinning sigstore 4.5.10 does not satisfy a 4.5.1 pin (exact comparison)" {
    printf 'sigstore==4.5.10 \\\n    --hash=sha256:00\n' >"$SIGSTORE_REQUIREMENTS_FILE"
    [ "$SIGSTORE_VERSION" = "4.5.1" ]

    run "$SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == *"task tools:sigstore-lock"* ]]
    [ ! -s "$UV_LOG" ]
    [ ! -s "$VERIFY_LOG" ]
}

@test "a missing requirements file fails closed naming the path and the lock task, before any uv call" {
    rm -f "$SIGSTORE_REQUIREMENTS_FILE"
    printf 'previous content\n' >"$CHECKSUMS_FILE"

    run "$SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == *"$SIGSTORE_REQUIREMENTS_FILE"* ]]
    [[ "$output" == *"task tools:sigstore-lock"* ]]
    [ ! -s "$UV_LOG" ]
    [ "$(cat "$CHECKSUMS_FILE")" = "previous content" ]
}

@test "only dir-mcp assets are ever verified" {
    run "$SCRIPT"
    [ "$status" -eq 0 ]

    # One "verify" line and one bundle-content line per dir-mcp platform
    # (4 each), and every bundle belongs to a dir-mcp release.
    [ "$(grep -c '^verify ' "$VERIFY_LOG")" -eq 4 ]
    [ "$(grep -c '^bundle-content: ' "$VERIFY_LOG")" -eq 4 ]
    [ "$(grep '^bundle-content: ' "$VERIFY_LOG" | grep -c 'https://github.com/agntcy/dir-mcp/releases/download/')" -eq 4 ]
}
