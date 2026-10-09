# Proposal

## Why

`scripts/lib/versions.sh` pins each local tool's *version*, but not its
*content*: `scripts/setup.sh` installs whatever bytes the download URL (or
the npm registry) serves on the day of install. A re-tagged release, a
compromised release asset, or a tampered mirror would install silently on
every developer machine and in CI. Issue #805 asks for SHA/checksum
pinning for local tools, matching what the repo already does for GitHub
Actions and container images (`pinned-external-references`).

## What Changes

- Pin a SHA-256 for every archive `setup.sh` downloads directly
  (actionlint, bats, node, shellcheck, shfmt, task, uv), for every
  supported OS/arch, in a new `scripts/lib/checksums.txt`. `setup.sh`
  verifies each download before unpacking it and fails closed on a
  mismatch or a missing pin.
- Move the download URLs into one shared helper (`scripts/lib/assets.sh`)
  so `setup.sh` and the checksum generator cannot disagree.
- Add `task tools:checksums` (`scripts/tools/update_checksums.bash`) to
  regenerate `checksums.txt` after a pin bump.
- Pin the npm-installed tools (openspec, renovate) with a committed
  `package-lock.json` under `scripts/lib/npm-tools/`, installed with `npm
  ci --ignore-scripts`, so every transitive package is integrity-checked.
  Their versions stay in `versions.sh` (one place for every tool version);
  the `package.json` is generated from those variables at install time.
  `task tools:npm-lock` regenerates the lockfile.
- Make Renovate keep the pins fresh: a `postUpgradeTasks` entry reruns
  the checksum and lockfile generators on any `versions.sh` bump.
- Update the rule, skills, Taskfile text, and tests that describe or
  exercise the above.

## Capabilities

### New Capabilities

### Modified Capabilities
- `repo-tooling`: tool downloads and npm installs are content-pinned and
  verified; the version single-source-of-truth requirement now names
  a generated `package.json` and committed lockfile for npm tools; Renovate refreshes the content pins.

## Impact

- `scripts/setup.sh`, `scripts/lib/{fetch,assets,npm_tools}.sh`,
  `scripts/lib/checksums.txt`, `scripts/lib/npm-tools/package-lock.json`,
  `scripts/tools/update_{checksums,npm_lock}.bash`, and their bats tests.
- `Taskfile.yaml`, `renovate.json`, `.github/workflows/renovate.yaml`
  (allowed post-upgrade command).
- `.agents/rules/meta/pinned-tool-versions.md`, the `manage-repo-tooling`,
  `setup-repo-tooling`, and `sync-renovate` skills.
- No runtime or application code is touched.
