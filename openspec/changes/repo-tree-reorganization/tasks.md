# Tasks

## 1. Move `.agents/rules/`

- [x] 1.1 `git mv` each rule file into `meta/`, `process/`, `always-apply/`,
      `quality/`, or `formatting/` per design.md
- [x] 1.2 Fix every rule-to-rule markdown link (both directions: links from a
      moved rule to another, and links from another rule into a moved one)
      for the new relative depth

## 2. Move `.agents/skills/`

- [x] 2.1 `git mv` each of the 13 hand-authored skill directories into
      `domain-lungo/`, `repo-tooling/`, or `quality-checks/` per design.md;
      leave the 6 `openspec-*` skills at their current flat path
- [x] 2.2 Fix every skill-to-rule link inside each moved `SKILL.md` for the
      new relative depth

## 3. Move `scripts/`

- [x] 3.1 `git mv` every `check_*.bash`, `fix_dashes.bash`, and
      `find_strings.bash` into `scripts/checks/`; `git mv` `lint_shell.bash`
      and `lint_workflows.bash` into `scripts/lint/`; leave `setup.sh`,
      `env.sh`, `ci-gate/`, and `lib/` in place
- [x] 3.2 Fix `REPO_ROOT` resolution from `$SCRIPT_DIR/..` to
      `$SCRIPT_DIR/../..` in the five scripts design.md names
      (`check_pinned_references.bash`, `check_workflow_permissions.bash`,
      `check_pipeline_exceptions.bash`, `lint_shell.bash`,
      `lint_workflows.bash`); verify no other moved script has an
      undiscovered depth-relative assumption

## 4. Fix every remaining reference

- [x] 4.1 Update `Taskfile.yaml`'s `cmds:` paths for every moved script
- [x] 4.2 Update `AGENTS.md`'s Rules/Skills tables to the new paths
- [x] 4.3 Update `.github/workflows/README.md` and any other prose
      referencing an old path (grep the whole repo for each moved file's old
      path, not just the files remembered as referencing it)
- [x] 4.4 Update `repo-tooling-foundations`'s and `repo-operation-governance`'s
      own proposal/design/spec/tasks files wherever they assert one of the
      old paths, so neither still-open change describes a path that no
      longer exists

## 5. Verification

- [x] 5.1 Run `task check:all` and `task dashes:check`; confirm both pass
      clean
- [x] 5.2 Run `openspec validate --strict` on `repo-tree-reorganization`,
      `repo-tooling-foundations`, and `repo-operation-governance`; confirm
      all three pass
- [x] 5.3 Grep the whole repo one more time for each old path to confirm
      zero remaining hits outside of git history/CHANGELOG
