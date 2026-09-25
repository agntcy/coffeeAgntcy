---
name: linting-github-workflows
description: >-
  Runs task workflows:lint (actionlint) against every file under
  .github/workflows/ and fixes what it reports. Use when writing or
  editing a workflow file, before finishing such a change, or when asked
  to lint GitHub Actions workflows.
---

# Linting GitHub workflows

## What this skill does

Runs `task workflows:lint` (defined in
[Taskfile.yaml](../../../Taskfile.yaml), wrapping
[scripts/lint_workflows.bash](../../../scripts/lint_workflows.bash)) to
check every file under `.github/workflows/` with actionlint, then fixes
whatever it reports. This is the exact command the "Validate" step in
[ci-gate.yaml](../../../.github/workflows/ci-gate.yaml) runs in CI. See
[.agents/rules/workflow-file-linting.md](../../rules/workflow-file-linting.md)
for the underlying rule.

## Workflow

```
- [ ] 1. If actionlint isn't already available, run: task setup && source
        scripts/env.sh (bootstraps it into .tools/bin/, pinned to
        scripts/lib/versions.sh)
- [ ] 2. Run: task workflows:lint
- [ ] 3. For a schema/syntax/structure finding, fix the workflow file
        directly
- [ ] 4. For a shellcheck finding inside a `run:` block, fix the
        underlying issue - or, if it's a genuine false positive (e.g. a
        variable only read through indirect expansion), add a targeted
        `# shellcheck disable=SCxxxx` comment with a reason next to that
        line
- [ ] 5. Re-run task workflows:lint to confirm it's clean
```

## Notes

- actionlint's shellcheck integration reports every severity (including
  shellcheck's own "warning" level, e.g. SC2034), unlike some CI wrappers
  that only fail above a configured severity threshold - so a finding
  showing up here is a real gate-blocker, not advisory.
- Don't reach for a blanket `-ignore` pattern to silence a whole class of
  finding; suppress the specific line with a reason instead, so a future
  genuine instance of that same check still gets caught.
