# Tasks

## 1. Core check script

- [x] 1.1 Implement `scripts/checks/check_helm_chart_versions.bash`: for
      each `Chart.yaml`, compare the newest commit touching the chart's
      contents (including `Chart.yaml` itself) against the newest commit
      changing its own top-level `version:` line (anchored `^version:`,
      no leading whitespace), across the chart's whole history with no
      lower bound and no CLI arguments. Verify: run it directly against
      this repo and confirm it exits 0 with "OK: every Helm chart's
      version reflects its latest content change".
- [x] 1.2 Write `scripts/checks/tests/check_helm_chart_versions.bats`
      against a real throwaway git fixture repo, covering: content
      changed then bumped (passes), content changed with no bump
      (fails), bump committed before a later content change (fails), a
      brand-new chart with no prior history (passes), a chart with no
      further changes since a clean state (passes), a nested
      `dependencies: - version:` line not counting as the chart's own
      bump (fails), and an invalid ref argument (exits non-zero). Verify:
      `bats scripts/checks/tests/check_helm_chart_versions.bats` - every
      case passes.
- [x] 1.3 Format and lint the new script. Verify: `task shell:lint`
      reports no findings for the new file.

## 2. Five-layer pipeline wiring

- [x] 2.1 Add the `helm:check-versions` task to `Taskfile.yaml`, in
      alphabetical position, wrapping the script with no arguments.
      Verify: `task helm:check-versions` runs the script and exits 0.
- [x] 2.2 Add
      `.agents/skills/quality-checks/checking-helm-chart-version-bumps/SKILL.md`,
      pointing an agent at the task (workflow: run the task, read what
      changed for any flagged chart, pick a bump level, edit
      `Chart.yaml`, re-run) - no base-ref/tag step, since the check takes
      none. Verify: `task links:check` passes for the new file's
      cross-links.
- [x] 2.3 Add `.agents/rules/quality/helm-chart-version-bump.md`,
      including the directory-rename limitation from design.md's
      Non-Goals stated explicitly (not left implicit). Index both the
      skill and the rule in `AGENTS.md`'s Skills/Rules tables
      (alphabetized within their section) and add
      `helm-chart-version-bump` to the "enforced in CI" list. Verify:
      `task links:check` passes; a read-through confirms both entries
      are alphabetized correctly.
- [x] 2.4 Wire `helm:check-versions` into
      `scripts/checks/check_all.bash`'s parallel list and its header
      comment. Update `scripts/checks/tests/check_all.bats` with a fake
      stand-in and `PASS: helm:check-versions` assertions in every
      relevant test case. Verify:
      `bats scripts/checks/tests/check_all.bats` passes.

## 3. CI wiring

- [x] 3.1 Add `fetch-depth: 0` to `checks.yaml`'s checkout step, with a
      comment explaining it's for full chart history, not for any git
      tag. Verify: `task workflows:lint` passes for the changed file.
- [x] 3.2 Run the full suite with the new check included. Verify:
      `task check:all`'s summary table shows `PASS: helm:check-versions`
      alongside every other check, with no chart in this repo flagged.

## 4. Docs

- [x] 4.1 Simplify `docs/RELEASE-OPS.md` Step 0 to the argument-free
      invocation (`task helm:check-versions`, no arguments), removing the
      manual last-release-tag lookup and per-chart diff steps it
      replaces. Verify: `task links:check` and `task dashes:check` pass
      for the changed file.
- [x] 4.2 Update `CONTRIBUTING.md`'s Helm-chart paragraph to match the
      argument-free check (drop the `-- <previous-release-tag>` example).
      Verify: `task dashes:check` passes for the changed file.
- [x] 4.3 Re-run `task check:all` once more after the docs changes to
      confirm nothing regressed. Verify: full summary table is all
      `PASS`.
