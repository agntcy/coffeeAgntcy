---
name: linting-shell-scripts
description: >-
  Runs task shell:lint (shellcheck + shfmt) against every shell script in
  the repo and fixes what it reports. Use when writing or editing a
  .sh/.bash file, before finishing such a change, or when asked to lint or
  format shell scripts.
---

# Linting shell scripts

## What this skill does

Runs `task shell:lint` (defined in [Taskfile.yaml](../../../Taskfile.yaml),
wrapping [scripts/lint_shell.bash](../../../scripts/lint_shell.bash)) to
check every shell script in the repo with shellcheck and shfmt, then fixes
whatever it reports. This is the same entry point the `shell-lint` CI job
uses. See
[.agents/rules/shell-script-linting.md](../../rules/shell-script-linting.md)
for the underlying rule.

## Workflow

```
- [ ] 1. Run: task shell:lint
- [ ] 2. For each shellcheck finding, fix the underlying issue (don't
        silence with a directive unless the flagged pattern is
        intentional - then use `# shellcheck disable=SCxxxx` with a
        comment on why, next to the line it applies to)
- [ ] 3. For shfmt diffs, run: task shell:fmt (rewrites in place), or fix
        by hand if only a couple of files changed
- [ ] 4. Re-run task shell:lint to confirm it's clean
```

## Notes

- `task shell:fmt` only fixes formatting - it never touches a shellcheck
  finding, so step 2 still needs doing even after running it.
- shfmt is pinned to `-i 4 -ci` (4-space indent, indented switch-case
  bodies) for this repo - don't reach for a different width or tab
  indentation even if a script predates the convention.
- A script that must do something shellcheck flags on purpose (e.g. an
  intentionally unquoted glob expansion) should suppress that one check
  with an inline `# shellcheck disable=SCxxxx` directive and a comment
  explaining why, rather than leaving the finding unresolved or disabling
  the check repo-wide.
