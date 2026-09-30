---
name: checking-workflow-permissions
description: >-
  Runs task workflows:check-permissions to find any GitHub Actions
  workflow file with a write-all grant or no declared permissions, and
  scopes it down to least privilege. Use when adding or editing a
  workflow file, or a job within one.
---

# Checking workflow permissions

## What this skill does

Runs `task workflows:check-permissions` (defined in
[Taskfile.yaml](../../../Taskfile.yaml), wrapping
[scripts/check_workflow_permissions.bash](../../../scripts/check_workflow_permissions.bash))
to flag any file under `.github/workflows/` that grants `write-all`
(workflow- or job-level) or leaves permissions undeclared entirely. This is
the same check `task check:all` runs as part of
[checks.yaml](../../../.github/workflows/checks.yaml). See
[.agents/rules/workflow-least-privilege.md](../../rules/workflow-least-privilege.md)
for the underlying rule.

## Workflow

```
- [ ] 1. Run: task workflows:check-permissions
- [ ] 2. For a file with no permissions: block at all, add one - either
        workflow-level if every job needs the same scopes, or per-job
        once they differ
- [ ] 3. For a write-all grant, replace it by naming only the scopes the
        job's steps actually use (usually contents: read for a
        checkout-and-run job; add anything broader only for a step that
        specifically calls for it, with a comment saying why)
- [ ] 4. Re-run task workflows:check-permissions to confirm it's clean
```

## Notes

- This script only checks the *shape* of the grant (write-all vs.
  undeclared vs. explicit) - it can't tell whether a granted scope is
  actually used by the steps. Read the steps by hand to judge that; prefer
  `read` over `write` and omitting a scope over granting `read` wherever
  the steps allow it.
- Once a workflow's jobs have different permission needs, move from one
  workflow-level `permissions:` block to per-job blocks instead of
  widening the shared one to cover the most demanding job.
