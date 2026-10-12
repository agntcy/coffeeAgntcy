# Tasks

## 1. Toolchain

- [x] 1.1 Pin `HELM_VERSION` in `scripts/lib/versions.sh` (alphabetical,
      with its Renovate annotation) and install helm unconditionally in
      `scripts/setup.sh`. Verify: `./scripts/setup.sh` installs it and
      `helm version` reports the pin.
- [x] 1.2 Extend `scripts/tests/setup.bats` and
      `scripts/lib/tests/versions.bats` for helm. Verify: both pass.

## 2. Update operation

- [x] 2.1 Implement `scripts/helm/update_chart_locks.bash` (optional root
      dir, helm from `.tools/bin` then PATH, isolated HELM_*_HOME, remove
      generated `charts/`, continue past a failing chart). Verify: runs
      clean against the real repo and leaves `git status` unchanged.
- [x] 2.2 Write `scripts/helm/tests/update_chart_locks.bats`. Verify: all
      cases pass.

## 3. Lock check

- [x] 3.1 Implement `scripts/checks/check_helm_chart_locks.bash`.
      Verify: exits 0 on this repo, and exits non-zero with the
      `file://` hint against the pre-fix corto state (extracted to a
      scratch git repo from the commit before the fix).
- [x] 3.2 Write `scripts/checks/tests/check_helm_chart_locks.bats`.
      Verify: all cases pass.

## 4. Pipeline wiring

- [x] 4.1 Add `helm:check-locks` and `helm:update-locks` tasks, and add
      the check to `check_all.bash` and `check_all.bats`. Verify: `task
      check:all` lists and runs it.
- [x] 4.2 Add the `checking-helm-chart-locks` skill and the
      `helm-chart-lock-sync` rule; index both in `AGENTS.md`; update
      `pre-finalize-checks.md`, `CONTRIBUTING.md`, the setup skill, and
      the workflows README. Verify: `task links:check`,
      `task pipeline:check-exceptions`, `task dashes:check` pass.

## 5. Final verification

- [x] 5.1 Run `task shell:lint`, `task tests:bash`, `task tests:coverage`
      and `task check:all`. Verify: everything passes except
      `helm:check-versions`, which fails on a pre-existing unbumped
      `corto-local-cluster` and is unrelated to this change.
