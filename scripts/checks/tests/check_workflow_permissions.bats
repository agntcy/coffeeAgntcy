#!/usr/bin/env bats
# Mocked end-to-end test for check_workflow_permissions.bash: the script
# computes REPO_ROOT from its own SCRIPT_DIR (two levels up) and then cds
# there before scanning .github/workflows/*.y*ml - so each test copies the
# script itself into a throwaway fixture repo under BATS_TEST_TMPDIR and
# runs that copy, which then cds into and scans the fixture repo instead
# of this real one.

SCRIPT_UNDER_TEST="$BATS_TEST_DIRNAME/../check_workflow_permissions.bash"

setup() {
    REPO_DIR="$BATS_TEST_TMPDIR/repo"
    mkdir -p "$REPO_DIR/scripts/checks" "$REPO_DIR/.github/workflows"
    cp "$SCRIPT_UNDER_TEST" "$REPO_DIR/scripts/checks/check_workflow_permissions.bash"
    chmod +x "$REPO_DIR/scripts/checks/check_workflow_permissions.bash"
}

run_check() {
    run "$REPO_DIR/scripts/checks/check_workflow_permissions.bash"
}

@test "passes for a workflow-level, explicit, scoped permissions block" {
    cat >"$REPO_DIR/.github/workflows/fake.yaml" <<'EOF'
name: Fake
on: push
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
EOF

    run_check
    [ "$status" -eq 0 ]
    [[ "$output" == *"Every workflow file declares explicit, non-write-all permissions."* ]]
}

@test "fails, naming the file, for a workflow-level write-all grant" {
    cat >"$REPO_DIR/.github/workflows/fake.yaml" <<'EOF'
name: Fake
on: push
permissions: write-all
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
EOF

    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"FAIL: .github/workflows/fake.yaml grants write-all"* ]]
}

@test "fails when a workflow has no permissions key at all anywhere" {
    cat >"$REPO_DIR/.github/workflows/fake.yaml" <<'EOF'
name: Fake
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
EOF

    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"has no workflow-level permissions: block, and job(s) missing their own: build"* ]]
}

@test "passes with workflow-level permissions alone even when jobs differ" {
    # One job declares its own (more restrictive) permissions, the other
    # declares none at all - per the script's actual logic, a workflow-level
    # permissions: key (column 0) short-circuits the whole file as covered,
    # so per-job presence/absence never gets checked once it exists.
    cat >"$REPO_DIR/.github/workflows/fake.yaml" <<'EOF'
name: Fake
on: push
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - run: echo hi
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
EOF

    run_check
    [ "$status" -eq 0 ]
    [[ "$output" == *"Every workflow file declares explicit, non-write-all permissions."* ]]
}

@test "fails for a job-level write-all grant" {
    cat >"$REPO_DIR/.github/workflows/fake.yaml" <<'EOF'
name: Fake
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    permissions: write-all
    steps:
      - run: echo hi
EOF

    run_check
    [ "$status" -eq 1 ]
    [[ "$output" == *"FAIL: .github/workflows/fake.yaml grants write-all"* ]]
}

@test "passes with a message when no workflow files exist" {
    rmdir "$REPO_DIR/.github/workflows"

    run_check
    [ "$status" -eq 0 ]
    [[ "$output" == *"No workflow files found under .github/workflows/."* ]]
}
