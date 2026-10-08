# Tasks

## 1. Spec correction

- [x] 1.1 Update the `repo-tooling` requirement's tool list and `PATH`
      directories via the delta in this change. Verify: `openspec validate
      toolchain-spec-drift` passes.

## 2. Consistency sweep

- [x] 2.1 Confirm every other surface already names the full toolchain
      (`Taskfile.yaml` setup task, `scripts/setup.sh` header,
      `setup-repo-tooling` skill). Verify: grep the repo for the tool
      list and confirm no surface omits `bats` or `renovate`.
- [x] 2.2 Run `task check:all`. Verify: every check passes.
