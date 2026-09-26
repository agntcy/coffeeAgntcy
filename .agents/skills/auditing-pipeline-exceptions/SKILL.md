---
name: auditing-pipeline-exceptions
description: >-
  Runs task pipeline:check-exceptions to confirm every rule listed in
  repo-operation-pipeline.md's "Known exceptions" section as needing no
  script/task/skill/CI layer still genuinely has none. Use before
  finishing a change that adds a skill, or when asked to audit the
  pipeline rule's exception list.
---

# Auditing pipeline exceptions

## What this skill does

Runs `task pipeline:check-exceptions` (defined in
[Taskfile.yaml](../../../Taskfile.yaml), wrapping
[scripts/check_pipeline_exceptions.bash](../../../scripts/check_pipeline_exceptions.bash))
to check every rule listed in
[.agents/rules/repo-operation-pipeline.md](../../rules/repo-operation-pipeline.md)'s
"Known exceptions" section (the "purely manual/visual conventions"
bucket - no script/task/skill/CI layer at all) for a skill that's since
grown into being that rule's own entry point without the rule being
promoted out of the list. This is the same check `task check:all` runs
as part of [checks.yaml](../../../.github/workflows/checks.yaml). See
[.agents/rules/repo-operation-pipeline.md](../../rules/repo-operation-pipeline.md)
for the underlying rule.

## Workflow

```
- [ ] 1. Run: task pipeline:check-exceptions
- [ ] 2. If it fails, it names the rule now in violation: either promote
        that rule out of the exception list (give it the script/task/
        skill/CI layers repo-operation-pipeline.md's main pattern
        describes, via the add-repo-operation skill), or, if the flagged
        skill's cross-link was a mistake (it named that rule as its
        "underlying rule" without actually being built for it), fix the
        skill's own cross-link instead
- [ ] 3. Re-run task pipeline:check-exceptions to confirm it's clean
```

## Notes

- The check's signal is narrow on purpose: a rule's filename appearing
  within a few lines of the phrase "underlying rule" in some
  `SKILL.md`, not just any mention of that filename anywhere. A skill
  can legitimately *mention* an exception-listed rule in passing (e.g.
  `add-repo-operation` tells agents to also apply
  `alphabetize-entity-lists.md` and `pre-finalize-checks.md` while
  adding an operation) without being that rule's own entry point - only
  the "underlying rule" cross-link means a skill was actually built for
  it.
- This only audits the "purely manual/visual conventions" exception
  bucket - the other four exception categories in
  `repo-operation-pipeline.md` (CI-only orchestration, bootstrap tooling
  itself, one-shot generative actions, a genuinely different execution
  model) each assert something different and aren't covered by this
  check.
