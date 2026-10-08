---
name: keep-changelog-current
description: >-
  When a change is visible to users of coffeeAgntcy (an application
  feature or behavior, its UI, configuration, environment variables,
  Compose files, Helm charts or images, the pattern library or event
  schema, a documented task or contribution process), add its entry to the
  Unreleased section of CHANGELOG.md in the same change. Apply as part of
  the final review of any non-trivial change.
---

# Keep the changelog current

## Rule

When a change is visible to users of coffeeAgntcy, add an entry for it
under `## Unreleased` in `CHANGELOG.md`, in the same change:

- Put it under the matching Keep a Changelog heading (`Added`, `Changed`,
  `Deprecated`, `Removed`, `Fixed`, `Security`), creating the heading if
  `Unreleased` doesn't have it yet.
- Describe the change for a user, not the diff: what they can now do or
  run, or must do differently, and in which project (Corto, Lungo,
  Recruiter) when it isn't repo-wide.
- Reference the PR in this repo that makes the change, as `(#123)`.
- If the entry is already there marked `(planned)`, update it to match
  what actually changed, add the PR number and remove the marker, instead
  of adding a second entry.
- For work that is planned but not merged yet, add an entry ending in
  `(planned)` only when asked to record planned content. Remove a
  `(planned)` entry when its work is dropped.
- Don't touch the `Target:` line or a released version's section: moving
  the target and cutting a version are release steps, covered in
  `CONTRIBUTING.md`'s "Releases" section and `docs/RELEASE-OPS.md`.

User-visible means an application feature or behavior added, changed or
removed; a change to its UI, configuration, environment variables,
Compose files, Helm charts or images; a change to the pattern library or
the event schema; and a change to a documented task or contribution
process. Internal changes with no effect on a user, such as a CI fix, a
test fix or a refactor, can be left out.

## Why

The changelog's `Unreleased` section is what the next monthly release
reports: when a version is cut, the release notes are generated from it.
An entry written later, from the commit history, is easy to miss or
describe wrongly, and a missed entry means the release says it shipped
less than it did.

## How to apply

- Check this alongside `keep-docs-consistent.md`: both are about leaving
  no surface describing the old state.
- This is a rule-only exception in
  `.agents/rules/meta/repo-operation-pipeline.md`'s terms: whether a change
  is user-visible is a judgment call, so there is no script or check for it.
