---
name: pinned-tool-versions
description: >-
  scripts/lib/versions.sh is the single source of truth for every tool
  version this repo installs locally into .tools/bin/; scripts/setup.sh's
  install-or-skip check for each tool must compare the installed version
  against that pin, not just whether the binary exists. Apply whenever
  adding, updating, or removing a pinned tool - see the
  `manage-repo-tooling` skill for the checklists this backs.
---

# Pinned tool versions

## Rule

Every tool this repo installs into `.tools/bin/` has its version pinned
exactly once, in
[`scripts/lib/versions.sh`](../../scripts/lib/versions.sh).
[`scripts/setup.sh`](../../scripts/setup.sh)'s install-or-skip check for
each tool must compare the *installed* version against that pin (via
`version_matches`, not just `[ -x "$BIN_DIR/$tool" ]`) and reinstall on any
mismatch.

## Why

A pin that `setup.sh` doesn't check for drift is a pin in name only:
bumping `scripts/lib/versions.sh` would silently do nothing on any machine
that already has the old binary at `.tools/bin/`, since presence alone
would satisfy the old check. `version_matches` strips a leading `v` from
both sides before comparing, because tools are inconsistent about printing
one (`shfmt --version` prints `v3.14.1`; `task --version` prints `3.53.1`
for a pin of `v3.53.1`).

## How to apply

- A new tool's install block needs the same `[ -x "$BIN_DIR/$tool" ] &&
  version_matches "<extracted version>" "$TOOL_VERSION"` guard as every
  existing one - copy the shape of an existing block, not just an
  existence check, or a future version bump on that tool will silently
  no-op.
- After bumping a pin, actually run `task setup` (not just edit the file)
  and confirm the tool's `--version`/`-version` output changed.
- None of "update a pin" / "add a tool" / "remove a tool" gets a dedicated
  CI check - they're one-shot maintenance actions, not standing
  invariants, matching the "purely generative, one-shot actions" exception
  in
  [`.agents/rules/repo-operation-pipeline.md`](repo-operation-pipeline.md).
  Running `task check:all` after any tooling change is what stands in for
  one: it exercises shellcheck/shfmt and actionlint indirectly, so a
  version bump that shifts their output surfaces immediately.
