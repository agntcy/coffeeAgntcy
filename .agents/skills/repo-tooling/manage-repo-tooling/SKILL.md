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
[`scripts/lib/versions.sh`](../../../../scripts/lib/versions.sh), add a new
tool to this repo's local `.tools/bin` toolchain, or remove one that's no
longer needed. This is a repo-maintainer activity on the toolchain's
*pins* - different from the `setup-repo-tooling` skill, which just runs
what's already pinned.

To just see which versions are pinned, run `task tools:versions` (a
read-only table of every pin in `scripts/lib/versions.sh`, with each tool's
pinned hash for this machine).

## Updating a pinned version

```
- [ ] 1. Edit the <TOOL>_VERSION in scripts/lib/versions.sh - the single source of truth, for every tool including openspec and renovate.
- [ ] 2. For a downloaded tool: run task tools:checksums; for openspec/renovate: run task tools:npm-lock. Then review the scripts/lib/checksums.txt diff (cross-check against the upstream project's published checksums where it has any). setup.sh rejects any archive whose URL has no pinned SHA-256, so skipping this makes step 3 fail.
- [ ] 3. Run: task setup (or ./scripts/setup.sh). It compares the installed version against the pin and reinstalls on any mismatch, so this actually picks up the bump - it isn't a no-op just because a binary already exists.
- [ ] 4. Confirm: <tool> --version (or -version) matches the new pin.
- [ ] 5. Run: task check:all - a version bump can change lint/format output (shellcheck/shfmt/actionlint findings can shift between versions).
```

## Introducing a new tool

```
- [ ] 1. Add <TOOL>_VERSION, with its `# renovate:` annotation line above it, to scripts/lib/versions.sh in alphabetical position (the install blocks in scripts/setup.sh stay in dependency order instead).
- [ ] 2. Add an install block to scripts/setup.sh, matching the shape of however the tool distributes itself: an official install script piped to sh (like task), a static binary release fetched via FETCH_VERIFIED + scripts/lib/platform.sh's OS/arch detection (like actionlint/shellcheck/shfmt) (also add its URL to asset_url and its name to ASSET_TOOLS in scripts/lib/assets.sh, then run task tools:checksums), or an npm package: add its pin to versions.sh, its entry to write_npm_tools_package_json in scripts/lib/npm_tools.sh, run task tools:npm-lock, and extend the existing npm ci block in setup.sh (like openspec/renovate - its version check and symlink, don't add a second npm install). Guard it the same way every existing block is guarded - see the pinned-tool-versions rule.
- [ ] 3. Wire whatever new script/task actually needs the tool - see the add-repo-operation skill if this is for a brand-new operation.
- [ ] 4. Update every place the toolchain is named: CONTRIBUTING.md, AGENTS.md, .agents/skills/repo-tooling/setup-repo-tooling/SKILL.md's tool list, Taskfile.yaml's setup task description.
- [ ] 5. Simulate a fresh clone: move .tools/ aside (mv .tools /tmp/tools-bak), run task setup, confirm it installs cleanly, then remove the backup once confirmed.
- [ ] 6. Run: task check:all.
```

## Removing a tool

```
- [ ] 1. Remove its install block from scripts/setup.sh and its _VERSION from scripts/lib/versions.sh (and, for an npm tool, its entry in scripts/lib/npm_tools.sh), then run task tools:checksums / task tools:npm-lock so its URLs and packages leave scripts/lib/checksums.txt and the lockfile.
- [ ] 2. Grep the whole repo for the tool's name and remove or update every mention - CONTRIBUTING.md, AGENTS.md, .agents/skills/repo-tooling/setup-repo-tooling/SKILL.md, Taskfile.yaml descriptions, any rule/skill/script that shells out to it.
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
