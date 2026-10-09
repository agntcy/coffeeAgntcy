---
name: pinned-tool-versions
description: >-
  scripts/lib/versions.sh is the single source of truth for every tool
  version this repo installs locally into .tools/bin/ (the npm tools'
  package.json is generated from it, next to a committed lockfile); scripts/setup.sh's
  install-or-skip check for each tool must compare the installed version
  against that pin, not just whether the binary exists, and every archive
  it downloads must match a SHA-256 pinned in scripts/lib/checksums.txt.
  Apply whenever
  adding, updating, or removing a pinned tool - see the
  `manage-repo-tooling` skill for the checklists this backs.
---

# Pinned tool versions

## Rule

Every tool this repo installs into `.tools/bin/` has its version pinned
exactly once, in
[`scripts/lib/versions.sh`](../../../scripts/lib/versions.sh) - the one file
to read to see which versions the repo runs, and the one to edit to change
them. That includes the npm tools (openspec, renovate): their `package.json`
is not committed but generated from those variables
([`scripts/lib/npm_tools.sh`](../../../scripts/lib/npm_tools.sh)).
[`scripts/setup.sh`](../../../scripts/setup.sh)'s install-or-skip check for
each tool must compare the *installed* version against that pin (via
`version_matches`, not just `[ -x "$BIN_DIR/$tool" ]`) and reinstall on any
mismatch.

Every archive `setup.sh` downloads directly is also pinned by SHA-256, in
[`scripts/lib/checksums.txt`](../../../scripts/lib/checksums.txt) (one
`<sha256>  <url>` line per archive, for every supported OS/arch). `setup.sh`
fetches through `FETCH_VERIFIED` (in
[`scripts/lib/fetch.sh`](../../../scripts/lib/fetch.sh)), which fails closed
on a mismatch or on a URL with no pinned line. The URLs themselves come from
[`scripts/lib/assets.sh`](../../../scripts/lib/assets.sh), shared with the
generator, so the two cannot drift. Regenerate with `task tools:checksums`.
npm tools are installed with `npm ci --ignore-scripts` from the committed
[`package-lock.json`](../../../scripts/lib/npm-tools/package-lock.json), so
every transitive package is integrity-checked; `npm ci` fails if the lockfile
no longer matches the versions.sh pins, and `setup.sh` reinstalls whenever the
lockfile changes, not only when a tool's own version does. Regenerate it with
`task tools:npm-lock`.

## Why

A pin that `setup.sh` doesn't check for drift is a pin in name only:
bumping `scripts/lib/versions.sh` would silently do nothing on any machine
that already has the old binary at `.tools/bin/`, since presence alone
would satisfy the old check. `version_matches` strips a leading `v` from
both sides before comparing, because tools are inconsistent about printing
one (`shfmt --version` prints `v3.14.1`; `task --version` prints `3.53.1`
for a pin of `v3.53.1`).

A version pin alone trusts whatever the download URL serves on the day of
install: a re-tagged release, a compromised release asset, or a tampered
mirror would install silently. The checksum pin makes that a loud failure
instead, and it is a different file from `versions.sh` on purpose, since
Renovate bumps versions but cannot compute hashes - a Renovate PR that
bumps a version fails `setup.sh` (and the `assets.bats` test) until
`task tools:checksums` is run on that branch and its output reviewed.
Renovate does this itself: a `postUpgradeTasks` entry in `renovate.json`
reruns `scripts/tools/update_checksums.bash` and
`scripts/tools/update_npm_lock.bash` on every `versions.sh` bump (the
self-hosted workflow allows exactly those two commands via
`RENOVATE_ALLOWED_COMMANDS`). Hashes computed that way are
trust-on-first-use at bump time, so the PR diff is where a reviewer
cross-checks them.

## How to apply

- A new tool's install block needs the same `[ -x "$BIN_DIR/$tool" ] &&
  version_matches "<extracted version>" "$TOOL_VERSION"` guard as every
  existing one - copy the shape of an existing block, not just an
  existence check, or a future version bump on that tool will silently
  no-op.
- After bumping openspec or renovate, run `task tools:npm-lock` and commit the
  lockfile diff (it uses the repo's own npm, never a global one).
- After bumping or adding a directly downloaded pin, run `task tools:checksums` first, review
  the diff (cross-check against the upstream project's published
  checksums where it has any), and commit `checksums.txt` with the bump.
- After bumping a pin, actually run `task setup` (not just edit the file)
  and confirm the tool's `--version`/`-version` output changed.
- None of "update a pin" / "add a tool" / "remove a tool" gets a dedicated
  CI check - they're one-shot maintenance actions, not standing
  invariants, matching the "purely generative, one-shot actions" exception
  in
  [`.agents/rules/meta/repo-operation-pipeline.md`](repo-operation-pipeline.md).
  Running `task check:all` after any tooling change is what stands in for
  one: it exercises shellcheck/shfmt and actionlint indirectly, so a
  version bump that shifts their output surfaces immediately.
