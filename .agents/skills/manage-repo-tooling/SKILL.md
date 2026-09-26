---
name: manage-repo-tooling
description: >-
  Update a pinned tool's version, introduce a new tool, or remove one from
  this repo's local toolchain (scripts/lib/versions.sh + scripts/setup.sh).
  Use when asked to bump a tool version, add a new CLI dependency, or drop
  one that's no longer used.
---

# Manage repo tooling

## When to use

When asked to bump a pinned version in
[`scripts/lib/versions.sh`](../../../scripts/lib/versions.sh), add a new
tool to this repo's local `.tools/bin` toolchain, or remove one that's no
longer needed. This is a repo-maintainer activity on the toolchain's
*pins* - different from the `setup-repo-tooling` skill, which just runs
what's already pinned.

## Updating a pinned version

```
- [ ] 1. Edit the <TOOL>_VERSION in scripts/lib/versions.sh - the single source of truth.
- [ ] 2. Run: task setup (or ./scripts/setup.sh). It compares the installed version against the pin and reinstalls on any mismatch, so this actually picks up the bump - it isn't a no-op just because a binary already exists.
- [ ] 3. Confirm: <tool> --version (or -version) matches the new pin.
- [ ] 4. Run: task check:all - a version bump can change lint/format output (shellcheck/shfmt/actionlint findings can shift between versions).
```

## Introducing a new tool

```
- [ ] 1. Add <TOOL>_VERSION to scripts/lib/versions.sh.
- [ ] 2. Add an install block to scripts/setup.sh, matching the shape of however the tool distributes itself: an official install script piped to sh (like task), a static binary release fetched via FETCH + scripts/lib/platform.sh's OS/arch detection (like actionlint/shellcheck/shfmt), or an npm package installed via the bootstrapped Node's npm --prefix .tools (like openspec - see how node/openspec are wired for the shape of a tool that needs its own runtime first). Guard it the same way every existing block is guarded - see the pinned-tool-versions rule.
- [ ] 3. Wire whatever new script/task actually needs the tool - see the add-repo-operation skill if this is for a brand-new operation.
- [ ] 4. Update every place the toolchain is named: CONTRIBUTING.md, AGENTS.md, .agents/skills/setup-repo-tooling/SKILL.md's tool list, Taskfile.yaml's setup task description.
- [ ] 5. Simulate a fresh clone: move .tools/ aside (mv .tools /tmp/tools-bak), run task setup, confirm it installs cleanly, then remove the backup once confirmed.
- [ ] 6. Run: task check:all.
```

## Removing a tool

```
- [ ] 1. Remove its install block from scripts/setup.sh and its _VERSION from scripts/lib/versions.sh.
- [ ] 2. Grep the whole repo for the tool's name and remove or update every mention - CONTRIBUTING.md, AGENTS.md, .agents/skills/setup-repo-tooling/SKILL.md, Taskfile.yaml descriptions, any rule/skill/script that shells out to it.
- [ ] 3. Confirm nothing still invokes it: grep scripts/ and .github/workflows/ for its binary name.
- [ ] 4. Simulate a fresh clone (see step 5 above) and run task check:all.
```

## Rules

- `scripts/lib/versions.sh` is the single source of truth for every pinned
  version - never hardcode one anywhere else (see the `setup-repo-tooling`
  skill).
- None of these three operations get a dedicated CI check - see the
  `pinned-tool-versions` rule for why, and what stands in for one.
- Keep every doc that names the toolchain in sync in the same change - see
  `self-review-after-change`.
