# Tasks

## 1. Checksum-verified downloads

- [x] 1.1 Add `scripts/lib/assets.sh` (`asset_url`, `ASSET_TOOLS`, `SUPPORTED_PLATFORMS`), add `sha256_of` and `FETCH_VERIFIED` to `scripts/lib/fetch.sh`, and switch every download in `scripts/setup.sh` to `FETCH_VERIFIED "$(asset_url ...)"` (shfmt via a temp dir); verify with `scripts/lib/tests/assets.bats` and `fetch.bats`
- [x] 1.2 Add `scripts/tools/update_checksums.bash`, the `tools:checksums` Taskfile task, and generate `scripts/lib/checksums.txt`; verify with `scripts/tools/tests/update_checksums.bats` and by cross-checking node/actionlint hashes against upstream's published checksums
- [x] 1.3 Extend `scripts/tests/setup.bats` with fixture checksums plus mismatch and missing-pin cases; verify `bats scripts/tests/setup.bats` passes
- [x] 1.4 Update the `pinned-tool-versions` rule and the `manage-repo-tooling` / `setup-repo-tooling` skills; verify with `task links:check`
- [x] 1.5 Verify end to end: move `.tools/` aside, run `./scripts/setup.sh`, confirm all seven downloads verify and install

## 2. Lockfile-pinned npm tools

- [x] 2.1 Keep `OPENSPEC_VERSION`/`RENOVATE_VERSION` in `scripts/lib/versions.sh`; add `scripts/lib/npm_tools.sh` (generates `package.json` from them), `scripts/tools/update_npm_lock.bash`, the `tools:npm-lock` task, and the committed `scripts/lib/npm-tools/package-lock.json`; verify the lockfile has `integrity` for every package and that regenerating it from the committed one is a no-op
- [x] 2.2 Change `setup.sh` to run `npm ci --ignore-scripts` into `.tools/npm` from a generated `package.json`, symlink the binaries into `.tools/bin`, and reinstall when the lockfile copy differs; verify with a fresh `setup.sh` run and `openspec --version` / `renovate --version`
- [x] 2.3 Update `setup.bats` (fake `npm ci`, lockfile-drift case, version-mismatch case), add `npm_tools.bats`, `update_npm_lock.bats`, and a `versions.bats` test that the lockfile matches the pins; verify `task tests:bash`
- [x] 2.4 Update the rule and skills for the lockfile and generated `package.json`; verify `task check:all`

## 3. Renovate keeps pins fresh

- [x] 3.1 In `renovate.json`, add the `postUpgradeTasks` (`scripts/tools/update_checksums.bash` and `update_npm_lock.bash`, `executionMode: branch`, `fileFilters` for `checksums.txt` and the lockfile) on the regex manager; verify `renovate-config-validator renovate.json`
- [x] 3.2 Add `RENOVATE_ALLOWED_COMMANDS` (one anchored command matching exactly those two scripts) to `.github/workflows/renovate.yaml`; verify `task workflows:lint` and `task workflows:check-permissions`
- [x] 3.3 Update the `sync-renovate` skill; verify `task links:check`
- [x] 3.4 Run `task check:all`; a live Renovate run (bump PR carrying refreshed pins) can only be confirmed after merge and is left to the maintainer
