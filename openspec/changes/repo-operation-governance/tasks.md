# Tasks

## 1. Confirm the documented-behavior requirements match reality

- [ ] 1.1 For each documentation-only requirement (five-layer pattern, the bootstrapping exception, `add-repo-operation`'s checklist, `manage-repo-tooling`'s three workflows, `pinned-tool-versions`' single-source-of-truth claim, `pre-finalize-checks`' mapping table), re-read the corresponding `.agents/rules/*.md`/`.agents/skills/*/SKILL.md` file and confirm it matches this spec's scenarios exactly; no code should need to change here - note and resolve any genuine drift rather than editing the spec to match it

## 2. Implement the exceptions-list self-audit

- [ ] 2.1 Write `scripts/check_pipeline_exceptions.bash`: a hardcoded array of the "purely manual/visual conventions" exception list (with a comment pointing at `repo-operation-pipeline.md`'s section to keep it in sync with), checking `.agents/skills/*/SKILL.md` for a reference to each rule's filename and failing (naming the rule) if found; verify it passes clean against the repo as it stands today, then verify it correctly fails by temporarily adding a fake reference to an exception-listed rule's filename into one skill file and confirming the failure names that rule, before reverting the temporary change
- [ ] 2.2 Add a `pipeline:check-exceptions` Taskfile task wrapping the script; verify `task --list` shows it and it runs the script unmodified
- [ ] 2.3 Add `.agents/skills/auditing-pipeline-exceptions/SKILL.md`, matching the shape of this repo's existing `checking-*` skills (what it does, workflow, notes); verify it cross-links the task and the rule
- [ ] 2.4 Cross-link the new script/task/skill from within `repo-operation-pipeline.md`'s existing "Known exceptions" section (no new rule file - see `design.md`); update `AGENTS.md`'s Skills table to index the new skill; verify every link resolves
- [ ] 2.5 Add `pipeline:check-exceptions` to `scripts/check_all.bash`'s parallel list; verify `task check:all` picks it up and still passes

## 3. Verification

- [ ] 3.1 Run `task check:all` and `task shell:lint`, including the new script; confirm both pass clean
