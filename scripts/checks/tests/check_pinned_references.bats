#!/usr/bin/env bats
# Mocked end-to-end test for check_pinned_references.bash: the script
# computes REPO_ROOT from its own SCRIPT_DIR (two levels up) and then cds
# there before scanning .github/workflows/*.y*ml, Dockerfiles, and
# docker-compose files - so each test copies the script itself into a
# throwaway fixture repo under BATS_TEST_TMPDIR and runs that copy, which
# then cds into and scans the fixture repo instead of this real one.

SCRIPT_UNDER_TEST="$BATS_TEST_DIRNAME/../check_pinned_references.bash"

# A 40-hex-character string, the shape a real commit SHA has.
FAKE_SHA="1234567890abcdef1234567890abcdef12345678"

# A 64-hex-character string, the shape a real sha256 digest has.
FAKE_DIGEST="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

setup() {
    REPO_DIR="$BATS_TEST_TMPDIR/repo"
    mkdir -p "$REPO_DIR/scripts/checks" "$REPO_DIR/.github/workflows"
    cp "$SCRIPT_UNDER_TEST" "$REPO_DIR/scripts/checks/check_pinned_references.bash"
    chmod +x "$REPO_DIR/scripts/checks/check_pinned_references.bash"
}

run_check() {
    run "$REPO_DIR/scripts/checks/check_pinned_references.bash"
}

# --- GitHub Actions `uses:` references -------------------------------------

@test "passes for a SHA-pinned uses: reference with a version comment" {
    cat >"$REPO_DIR/.github/workflows/fake.yaml" <<EOF
name: Fake
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@${FAKE_SHA} # v4.4.0
EOF

    run_check
    [ "$status" -eq 0 ]
    [[ "$output" == *"All action, reusable-workflow, and image references are pinned"* ]]
}

@test "fails, naming the line, for an unpinned tag uses: reference" {
    cat >"$REPO_DIR/.github/workflows/fake.yaml" <<'EOF'
name: Fake
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
EOF

    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *".github/workflows/fake.yaml"* ]]
    [[ "$output" == *"'v4' is not a full commit SHA"* ]]
}

@test "fails for a SHA-pinned uses: reference missing a version comment" {
    cat >"$REPO_DIR/.github/workflows/fake.yaml" <<EOF
name: Fake
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@${FAKE_SHA}
EOF

    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"SHA-pinned but missing a version comment nearby"* ]]
}

@test "skips a local action/reusable workflow reference (uses: ./...)" {
    cat >"$REPO_DIR/.github/workflows/fake.yaml" <<'EOF'
name: Fake
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: ./.github/actions/local-thing
EOF

    run_check
    [ "$status" -eq 0 ]
}

@test "passes when an unpinned uses: reference has a pin-exempt comment with a reason" {
    cat >"$REPO_DIR/.github/workflows/fake.yaml" <<'EOF'
name: Fake
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4 # pin-exempt: intentionally floating for this test
EOF

    run_check
    [ "$status" -eq 0 ]
}

@test "fails when a pin-exempt comment states no reason" {
    cat >"$REPO_DIR/.github/workflows/fake.yaml" <<'EOF'
name: Fake
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4 # pin-exempt:
EOF

    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"'pin-exempt' comment must state a reason"* ]]
}

# --- docker:// action references --------------------------------------------

@test "passes for a docker:// action digest-pinned with an embedded tag and no comment" {
    cat >"$REPO_DIR/.github/workflows/fake.yaml" <<EOF
name: Fake
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: docker://alpine:3.19@sha256:${FAKE_DIGEST}
EOF

    run_check
    [ "$status" -eq 0 ]
}

@test "fails for a docker:// action digest-pinned with no embedded tag and no comment" {
    cat >"$REPO_DIR/.github/workflows/fake.yaml" <<EOF
name: Fake
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: docker://alpine@sha256:${FAKE_DIGEST}
EOF

    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"has no tag embedded and no version comment nearby"* ]]
}

@test "passes for a docker:// action digest-pinned with no embedded tag but a version comment" {
    cat >"$REPO_DIR/.github/workflows/fake.yaml" <<EOF
name: Fake
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: docker://alpine@sha256:${FAKE_DIGEST} # 3.19
EOF

    run_check
    [ "$status" -eq 0 ]
}

# --- Dockerfile `FROM` instructions ------------------------------------------

@test "passes for a digest-pinned image, a multi-stage self-reference, and FROM scratch" {
    mkdir -p "$REPO_DIR/build"
    cat >"$REPO_DIR/build/Dockerfile" <<EOF
FROM golang:1.21@sha256:${FAKE_DIGEST} AS builder
FROM builder
FROM scratch
COPY --from=builder /app /app
EOF

    run_check
    [ "$status" -eq 0 ]
    [[ "$output" == *"All action, reusable-workflow, and image references are pinned"* ]]
}

@test "fails for a Dockerfile FROM with an unpinned third-party tag" {
    mkdir -p "$REPO_DIR/build"
    cat >"$REPO_DIR/build/Dockerfile" <<'EOF'
FROM golang:1.21
EOF

    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"'golang:1.21' is not pinned to an image digest"* ]]
}

# --- docker-compose `image:` fields ------------------------------------------

@test "does not flag this repo's own image prefix with a floating tag" {
    cat >"$REPO_DIR/docker-compose.yaml" <<'EOF'
services:
  roaster:
    image: ghcr.io/agntcy/coffee-agntcy/roaster:latest
EOF

    run_check
    [ "$status" -eq 0 ]
}

@test "fails for a genuinely unpinned third-party compose image" {
    cat >"$REPO_DIR/docker-compose.yaml" <<'EOF'
services:
  cache:
    image: nginx:latest
EOF

    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"'nginx:latest' is not pinned to an image digest"* ]]
}
