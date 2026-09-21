---
name: workflow-least-privilege
description: >-
  Every GitHub Actions workflow must declare explicit permissions scoped to
  only what its steps actually need - never write-all, never left
  undeclared, scoped per-job once jobs' needs differ. Apply whenever adding
  or editing a workflow file.
---

# Workflow least privilege

## Rule

Every file under `.github/workflows/` must declare an explicit
`permissions:` block that grants only the scopes its steps actually use, at
the narrowest level that still covers every job:

- Never rely on the absence of a `permissions:` key - that falls back to
  whatever the default `GITHUB_TOKEN` permissions happen to be for this
  repo/org, which isn't visible from the workflow file itself and can
  change independently of it.
- Never use `write-all` - it's a shorthand for granting every scope write
  access, the opposite of naming only what's needed.
- Prefer a workflow-level `permissions:` block only while every job in the
  file needs the same scopes. Once a workflow gains jobs with different
  needs, scope `permissions:` per job instead of letting one workflow-level
  grant over-provision every job to cover the most demanding one.
- Grant `read` instead of `write`, and omit a scope entirely instead of
  granting `read`, wherever the steps allow it. `contents: read` is usually
  the only scope a checkout-and-run job needs; add anything broader
  (`pull-requests: write`, `actions: read`, `packages: write`, etc.) only
  for a step that specifically calls for it, and say why in a comment - see
  [.github/workflows/ci-gate.yaml](../../.github/workflows/ci-gate.yaml) for
  an existing example of a narrowly scoped block (`contents: read`,
  `actions: read`).

## Why

A workflow's `GITHUB_TOKEN` is scoped to the whole repository by default
whenever a repo/org hasn't tightened its own default token permissions -
and even where it has, a workflow file that doesn't say so itself is
trusting a setting that lives outside the file and outside version control.
A compromised or vulnerable action (or a step that shells out to something
untrusted) can only do as much damage as the token it's handed; narrowing
that token to exactly what the job's steps use is the cheapest available
blast-radius control, and it costs nothing when steps are read-only or use
a single well-known API.

## How to apply

- There is no automated check for this yet, so review it by hand whenever a
  workflow file is added or edited: read every step, list the scopes they
  actually touch, and compare that against the declared `permissions:`
  block.
- When a new job needs a scope no existing job has, add it to that job
  alone rather than widening a shared workflow-level block.
