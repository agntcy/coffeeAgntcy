---
name: add-repo-operation
description: >-
  Guides adding a new repository operation (a check, validation, or piece
  of tooling) through this repo's standard script -> Taskfile task ->
  skill -> CI enforcement -> rule pipeline. Use when asked to add a new
  check, validation, or tool to this repo, or to audit whether an existing
  one is complete.
---

# Add a repository operation

## When to use

Whenever asked to add a new check, validation, or piece of tooling to this
repo, or to audit whether an existing one already follows the pipeline in
[`.agents/rules/repo-operation-pipeline.md`](../../rules/repo-operation-pipeline.md).

## Reference example

Use shell script linting as the concrete template to copy the shape of -
it has every layer:

| Layer | Shell-linting's version |
|---|---|
| Script | `scripts/lint_shell.bash` |
| Taskfile task | `shell:lint` / `shell:fmt` in `Taskfile.yaml` |
| Skill | `.agents/skills/linting-shell-scripts/SKILL.md` |
| CI enforcement | One of the parallel checks in `scripts/check_all.bash`, run via `task check:all` in `.github/workflows/checks.yaml` |
| Rule | `.agents/rules/shell-script-linting.md` |

## Steps

```
- [ ] 1. Write the script under scripts/ as scripts/<name>.bash (or scripts/lib/ for a shared helper) - resolve any tool it needs via .tools/bin first, falling back to PATH (see lint_shell.bash's resolve_tool for the pattern).
- [ ] 2. Add a Taskfile task that wraps it and nothing else.
- [ ] 3. Add a skill under .agents/skills/<name>/SKILL.md that points an agent at the task, not the script.
- [ ] 4. If it's a check/invariant (not a one-shot generative action): add it to scripts/check_all.bash's parallel list, so `task check:all` and the "Checks" CI workflow both pick it up with no other file needing to change - or fold it into ci-gate.yaml's "Validate" step if it's specifically a workflow-file check. Only give it its own workflow file if it has a genuinely different execution model (see "Known exceptions" in the rule) - ci-gate.yaml waits on any such new workflow automatically, no manual list to update there either.
- [ ] 5. Add a rule under .agents/rules/<name>.md documenting the convention and cross-linking the other four layers, then index both the skill and the rule in AGENTS.md's tables (alphabetized - see .agents/rules/alphabetize-entity-lists.md).
- [ ] 6. Add a row to .agents/rules/pre-finalize-checks.md if it's a check.
```

## After adding it

```
- [ ] 1. Run the new task directly to confirm it works: task <name>
- [ ] 2. Run task shell:lint if you added or changed a script.
- [ ] 3. Run task workflows:lint if you added or changed a workflow file.
- [ ] 4. Run task check:all to confirm it runs alongside everything else without breaking the parallel run.
- [ ] 5. If it landed in checks.yaml or ci-gate.yaml, actionlint the changed workflow file and confirm the job's bootstrap + task invocation actually runs clean locally first.
```

## Rules

- Default to folding a new check into `scripts/check_all.bash`, not a new workflow file - that's what keeps `checks.yaml` a single bootstrap plus a single parallel run instead of drifting back into one workflow per check.
- Don't force a dedicated workflow file onto something that fits one of the existing ones just because it feels more "official."
- Don't force CI enforcement of any kind onto a purely generative, one-shot action (e.g. a tooling version bump - see `manage-repo-tooling`) - there's nothing standing left to check once it's run.
- When something looks like it should skip a layer, name which exception category it falls under (see "Known exceptions" in
  [`.agents/rules/repo-operation-pipeline.md`](../../rules/repo-operation-pipeline.md)) rather than silently doing a partial job.
